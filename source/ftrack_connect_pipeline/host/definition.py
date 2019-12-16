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
            force_mode=constants.REMOTE_EVENT_MODE
        )

    def parse_dictonary(self, data, valueFilter, newList):
        if isinstance(data, dict):
            if data.get('type') == valueFilter:
                newList.append(data)
            else:
                for key, value in data.items():
                    self.parse_dictonary(value, valueFilter, newList)
        if isinstance(data, list):
            for item in data:
                self.parse_dictonary(item, valueFilter, newList)

    def validate_result(self, data):
        plugins_l = []
        self.parse_dictonary(data, 'plugin', plugins_l)
        print plugins_l
        invalid_plugins = self.validate_plugins(plugins_l)

        components_l = []
        self.parse_dictonary(data, 'component', components_l)
        invalid_components = self.validate_components(plugins_l)

        packages_l = []
        self.parse_dictonary(data, 'package', packages_l)
        invalid_packages = self.validate_packages(plugins_l)

        self.cleanDefinitions(invalid_plugins, invalid_components, invalid_packages)


    '''def validate_plugins(self, data):
        for plugin in data:

        if not self._discover_plugin(context_plugin, constants.CONTEXT):
            self.logger.warning(
                'Could not discover plugin {} for {} in {}'.format(
                    context_plugin['plugin'], constants.CONTEXT, package_name
                )
            )
        return list of plugins to delete

    def validate_components(self, data):
        pass
    def validate_packages(self, data):
        pass

    def cleanDefinitions(self):
        pass

    def _discover_plugin(self, plugin, plugin_type):
        #Run *plugin*, *plugin_type*, with given *options*, *data* and *context*
        plugin_name = plugin['plugin']

        data = {
            'pipeline': {
                'plugin_name': plugin_name,
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

        return plugin_result'''

class DefintionManager(object):
    '''class wrapper to contain all the definition managers.'''

    def __init__(self, event_manager, host):
        super(DefintionManager, self).__init__()

        self.session = event_manager.session

        self.definitions = BaseDefinitionManager(event_manager, host)

        self.json_definitions = self.definitions.result()
