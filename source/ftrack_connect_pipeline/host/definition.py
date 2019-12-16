# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import logging
import ftrack_api

from ftrack_connect_pipeline.event import EventManager
from functools import partial
from ftrack_connect_pipeline import constants, utils
import uuid

logger = logging.getLogger(__name__)

mapping = {'package': 'packages', 'publisher': 'publishers',
           'loader': 'loaders', 'object': 'schemas'}


def provide_host_information(hostid, definitions, event):
    '''return the current hostid'''
    print "provide host information has been called"
    logger.debug('providing host_id: {}'.format(hostid))
    context_id = utils.get_current_context()
    host_dict = {
        'host_id': hostid,
        'context_id': context_id,
        'definitions':definitions
    }
    return host_dict


class BaseDefinitionManager(object):

    def result(self, *args, **kwargs):
        '''Return the result definitions.'''
        return self.__registry

    def __init__(self, event_manager, host):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(BaseDefinitionManager, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        hostid = '{}-{}'.format(host, uuid.uuid4().hex)

        self.hostid = hostid
        self.__registry = {}
        self.host = host
        self.session = event_manager.session
        self.event_manager = event_manager
        self.register()

    def on_register_definition(self, event):
        '''Register definition coming from *event* and store them.'''
        raw_result = event['data']
        #print "on register definition ---> {}".format(raw_result)
        result = raw_result

        if not result:
            return

        parsedResult = self._parese_json(result, self.host)

        #self.validate_result(parsedResult)
        # validate here

        self.__registry = parsedResult

        handle_event = partial(provide_host_information, self.hostid, parsedResult)
        self.logger.info('host {} ready'.format(self.hostid))
        self.session.event_hub.subscribe(
            'topic={}'.format(
                constants.PIPELINE_DISCOVER_HOST
            ),
            handle_event
        )

    def _parese_json(self, jsonResult, host):
        parsedJson = {}
        for definition in jsonResult:
            if definition['type'] in mapping.keys():
                definitionType = mapping[definition['type']]
            else:
                definitionType = definition['type']
            if parsedJson.has_key(definitionType):
                if definition.has_key('host'):
                    if definition.get('host') == host:
                        parsedJson[definitionType][definition['host']] = [definition]
                else:
                    parsedJson[definitionType].append(definition)
            else:
                if definition.has_key('host'):
                    if definition.get('host') == host:
                        parsedJson[definitionType] = [definition]
                else:
                    parsedJson[definitionType] = [definition]
        return parsedJson

    def register(self):
        '''register package'''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': "definition"
                }
            }
        )

        self.event_manager.publish(
            event,
            self.on_register_definition,
            remote=True
        )

    '''def validate_result(self, data):
        for definition_l in data.values():
            for definition_d in definition_l:
                for values_l in definition_d.values():
                    for values_d in values_l:
                        if isinstance(values_d, dict):
                            if values_d['type'] == 'plugin':
                                print "plugin"
                                print "this is a plugin ---> {}".format(values_d)'''
    '''def validate_plugin(self):

    def validate_plugins(self, data):
        # discover context plugins
        package_name = data['package']
        context_plugins = data[constants.CONTEXT]
        for context_plugin in context_plugins:
            if not self._discover_plugin(context_plugin, constants.CONTEXT):
                self.logger.warning(
                    'Could not discover plugin {} for {} in {}'.format(
                        context_plugin['plugin'], constants.CONTEXT, package_name
                    )
                )
                return False

        # discover component plugins
        publisher_components = data[constants.COMPONENTS]
        for publisher_component in publisher_components:
            for publisher_stage in publisher_component['stages']:
                for component_stage, component_plugins in publisher_stage.items():
                    for component_plugin in component_plugins:
                        if not self._discover_plugin(component_plugin, component_stage):
                            self.logger.warning(
                                'Could not discover plugin {} for stage {} in {}'.format(
                                    component_plugin['plugin'], component_stage, package_name
                                )
                            )
                            return False

        # get publish plugins
        publisher_plugins = data[constants.PUBLISHERS]
        for publisher_plugin in publisher_plugins:
            if not self._discover_plugin(publisher_plugin, constants.PUBLISHERS):
                self.logger.warning(
                    'Could not discover plugin {} for {} in {}'.format(
                        publisher_plugin['plugin'], constants.PUBLISHERS, package_name
                    )
                )
                return False

        return True'''


class DefintionManager(object):
    '''class wrapper to contain all the definition managers.'''

    def __init__(self, event_manager, host):
        super(DefintionManager, self).__init__()

        self.session = event_manager.session

        self.definitions = BaseDefinitionManager(event_manager, host)

        self.json_definitions = self.definitions.result()
