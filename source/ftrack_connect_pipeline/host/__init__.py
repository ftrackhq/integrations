# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import ftrack_api
import logging

from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import Runner
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

        self.event_manager.subscribe(
            '{} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_HOST_RUN, self.hostid
            ),
            self.run
        )

    def run(self, event):
        self.logger.info('HOST RUN {}'.format(event['data']))
        # Runner(self.event_manager....)

    def on_register_definition(self, event):
        '''Register definition coming from *event* and store them.'''
        raw_result = event['data']

        if not raw_result:
            return

        validated_result = self.validate_result(raw_result)

        # validate here

        self.__registry = validated_result

        handle_event = partial(provide_host_information, self.hostid,
                               validated_result)
        self.event_manager.subscribe(
            constants.PIPELINE_DISCOVER_HOST,
            handle_event
        )

        self.logger.info('host {} ready.'.format(self.hostid))

    def validate_result(self, data):
        #plugin Validation
        invalid_publishers_idxs = self.validate_publishers_plugins(data['publishers'])
        if invalid_publishers_idxs:
            print "invalid_publishers_idxs --> {}".format(invalid_publishers_idxs)
            for idx in invalid_publishers_idxs:
                data['publishers'].pop(idx)

        invalid_loaders_idxs = self.validate_loaders_plugins(data['loaders'])
        if invalid_loaders_idxs:
            print "invalid_loaders_idxs --> {}".format(invalid_loaders_idxs)
            for idx in invalid_loaders_idxs:
                data['loaders'].pop(idx)

        return data

    def validate_publishers_plugins(self, publishers):
        idxs_to_pop = []
        for definition in publishers:
            valid_definition = True
            # context plugins
            if not self.vaildate_context_plugins(definition[constants.CONTEXT], definition["name"]):
                valid_definition = False
            if not self.validate_component_plugins(definition[constants.COMPONENTS], definition["name"]):
                valid_definition = False
            if not self.vaildate_publish_plugins(definition[constants.PUBLISHERS], definition["name"]):
                valid_definition = False
            if not valid_definition:
                idx = publishers.index(definition)
                idxs_to_pop.append(idx)
                self.logger.warning('The definition {} from type {} contains invalid plugins '
                                    'and will not be used'.format(definition["name"], 'publishers'))

        return idxs_to_pop or None

    def validate_loaders_plugins(self, loaders):
        idxs_to_pop = []
        for definition in loaders:
            valid_definition = True
            # context plugins
            if not self.validate_component_plugins(definition[constants.COMPONENTS], definition["name"]):
                valid_definition = False
            if not valid_definition:
                idx = loaders.index(definition)
                idxs_to_pop.append(idx)
                self.logger.warning('The definition {} from type {} contains invalid plugins '
                                    'and will not be used'.format(definition["name"], 'publishers'))

        return idxs_to_pop or None

    def vaildate_context_plugins(self, plugin_list, definition_name):
        is_valid = True
        for context_plugin in plugin_list:
            if not self._discover_plugin(context_plugin, constants.CONTEXT):
                is_valid = False
                self.logger.warning('Could not discover plugin {} for {} in {}'.format(
                    context_plugin['plugin'], constants.CONTEXT, definition_name))
        return is_valid

    def validate_component_plugins(self, plugin_list, definition_name):
        # components plugins
        is_valid = True
        for component in plugin_list:
            for component_stage in component['stages']:
                for stage_name, component_plugins in component_stage.items():
                    for component_plugin in component_plugins:
                        if not self._discover_plugin(component_plugin, stage_name):
                            is_valid = False
                            self.logger.warning('Could not discover plugin {} for stage {} in {}'.format(
                                component_plugin['plugin'], stage_name, definition_name))
        return is_valid

    def vaildate_publish_plugins(self, plugin_list, definition_name):
        is_valid = True
        for publisher_plugin in plugin_list:
            if not self._discover_plugin(publisher_plugin, constants.PUBLISHERS):
                is_valid = False
                self.logger.warning('Could not discover plugin {} for {} in {}'.format(
                    publisher_plugin['plugin'], constants.PUBLISHERS, definition_name))
        return is_valid

    def _discover_plugin(self, plugin, plugin_type):
        '''Run *plugin*, *plugin_type*, with given *options*, *data* and *context*'''
        plugin_name = plugin['plugin']

        data = {
            'pipeline': {
                'plugin_name': plugin_name,
                'plugin_type': plugin_type,
                'type': 'plugin',
                'host': self.host
            }
        }
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_PLUGIN_TOPIC,
            data=data
        )

        plugin_result = self.session.event_hub.publish(
            event,
            synchronous=True
        )

        if plugin_result:
            plugin_result = plugin_result[0]

        return plugin_result

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




