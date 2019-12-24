# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import ftrack_api
import logging

from ftrack_connect_pipeline.host import runner
from ftrack_connect_pipeline.host import validation
from ftrack_connect_pipeline import constants, utils


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
        # self.logger.info('HOST RUN {}'.format(event['data']))
        data = event['data']['pipeline']['data']

        try:
            validation.validate_schema(self.__registry['schemas'], data)
        except Exception as error:
            self.logger.error("Can't validate the data {} error: {}".format(data, error))
            return False

        asset_type = self.get_asset_type_from_packages(self.__registry['packages'], data['package'])
        engine = data['_config']['engine']
        MyEngine = runner.getEngine(runner.BaseRunner, engine)
        engine_runner = MyEngine(self.event_manager, self.host, self.hostid, asset_type)
        runnerResult = engine_runner.run(data)

        if runnerResult == False:
            self.logger.error("Couldn't publish the data {}".format(data))

        return runnerResult

    def get_asset_type_from_packages(self, packages, data_package):
        for package in packages:
            if package["name"] == data_package:
                return package["asset_type"]

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
        # plugin Validation

        plugin_validator = validation.PluginDiscoverValidation(self.session, self.host)

        invalid_publishers_idxs = plugin_validator.validate_publishers_plugins(data['publishers'])
        if invalid_publishers_idxs:
            for idx in invalid_publishers_idxs:
                data['publishers'].pop(idx)

        invalid_loaders_idxs = plugin_validator.validate_loaders_plugins(data['loaders'])
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
        #TODO: Why is the remote mode comented here???
        self.event_manager.publish(
            event,
            self.on_register_definition,
            # mode=constants.REMOTE_EVENT_MODE
        )




