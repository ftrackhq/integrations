# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import ftrack_api
import logging

from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import Runner
from ftrack_connect_pipeline.host import validation
from ftrack_connect_pipeline import constants, utils

from jsonschema import validate as _validate_jsonschema


from functools import partial


logger = logging.getLogger(__name__)


def provide_host_information(hostid, definitions, event):
    '''return the current hostid'''
    logger.debug('providing host_id: {}'.format(hostid))
    context_id = utils.get_current_context()
    host_dict = {
        'host_id': hostid,
        'context_id': context_id,
        'definitions': definitions
    }
    return host_dict



class Host(object):

    def __init__(self, event_manager, host):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        hostid = '{}-{}'.format(host, uuid.uuid4().hex)
        self.logger.info(
            'initializing Host {}'.format(hostid)
        )
        self.hostid = hostid
        self.__registry = {}
        self.host = host
        self.session = event_manager.session
        self.event_manager = event_manager
        self.register()

    def run(self, event):
        self.logger.info('HOST RUN {}'.format(event['data']))

        definitionType = None
        if event['data'].get('type'):
            definitionType = event['data']['type']
        else:
            self.logger.error("Invalid definition: The definition has no key type. "
                              "Definition: {}".format(event["data"]))

        schema = self.get_schema(definitionType)
        try:
            self.validate_schema(schema, event['data'])
        except Exception as error:
            self.logger.error(error)
            return False

        return True

    def get_schema(self, definition_type):
        for schema in self.__registry['schemas']:
            if schema['title'] == constants.LOADER_SCHEMA:
                if definition_type == 'loader':
                    return schema
            elif schema['title'] == constants.PUBLISHER_SCHEMA:
                if definition_type == 'publisher':
                    return schema
            elif schema['title'] == constants.PACKAGE_SCHEMA:
                if definition_type == 'package':
                    return schema
        return None

    def validate_schema(self, schema, definition):
        _validate_jsonschema(schema, definition)

    def on_register_definition(self, event):
        '''Register definition coming from *event* and store them.'''
        raw_result = event['data']

        if not raw_result:
            return

        validated_result = self.validate(raw_result)

        for key, value in validated_result.items():
            logger.info('Valid packages : {} : {}'.format(key, len(value)))

        self.__registry = validated_result

        handle_event = partial(
            provide_host_information,
            self.hostid,
            validated_result
        )

        self.event_manager.subscribe(
            constants.PIPELINE_DISCOVER_HOST,
            handle_event
        )

        self.event_manager.subscribe(
            '{} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_HOST_RUN, self.hostid
            ),
            self.run
        )
        self.logger.info('host {} ready.'.format(self.hostid))

    def validate(self, data):
        #plugin Validation

        pluginValidator = validation.PluginValidation(self.session, self.host)

        invalid_publishers_idxs = pluginValidator.validate_publishers_plugins(data['publishers'])
        if invalid_publishers_idxs:
            for idx in invalid_publishers_idxs:
                data['publishers'].pop(idx)

        invalid_loaders_idxs = pluginValidator.validate_loaders_plugins(data['loaders'])
        if invalid_loaders_idxs:
            for idx in invalid_loaders_idxs:
                data['loaders'].pop(idx)

        return data

    def register(self):
        '''register package'''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': "definition",
                    'host': self.host
                }
            }
        )

        self.event_manager.publish(
            event,
            self.on_register_definition,
            mode=constants.REMOTE_EVENT_MODE
        )




