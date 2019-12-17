# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import logging
import ftrack_api
import copy

from ftrack_connect_pipeline import constants, utils
from jsonschema import validate as _validate
from functools import partial

logger = logging.getLogger(__name__)


def provide_host_information(hostid, definitions, event):
    '''return the current hostid'''
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
        self.logger.info('initializing Definition manager {}'.format(hostid))
        self.hostid = hostid
        self.__registry = {}
        self.host = host
        self.session = event_manager.session
        self.event_manager = event_manager
        self.register()

    def on_register_definition(self, event):
        '''Register definition coming from *event* and store them.'''
        # print 'EVENT', event
        raw_result = event['data']

        if not raw_result:
            return

        result = self.filter_by_host(raw_result, self.host)

        if not result:
            return
        self.validate_result(result)

        # validate here

        self.__registry = result

        handle_event = partial(provide_host_information, self.hostid, result)
        self.session.event_hub.subscribe(
            'topic={}'.format(
                constants.PIPELINE_DISCOVER_HOST
            ),
            handle_event
        )
        self.logger.info('host {} ready.'.format(self.hostid))

    def filter_by_host(self, json_data, host):
        json_copy = copy.deepcopy(json_data)
        for definition_name, values in json_data.items():
            for definition in values:
                if definition.get('host') and definition.get('host') != host:
                    idx = json_copy[definition_name].index(definition)
                    pop_result = json_copy[definition_name].pop(idx)
        return json_copy

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
            mode=constants.REMOTE_EVENT_MODE
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

        self.validate_definitions(data)

        plugins_l = []
        self.parse_dictonary(data, 'plugin', plugins_l)
        invalid_plugins = self.validate_plugins(plugins_l)

        components_l = []
        self.parse_dictonary(data, 'component', components_l)
        package_components_l = []
        self.parse_dictonary(data, 'package_component', package_components_l)
        invalid_components = self.validate_components(components_l, package_components_l)

        asset_types = [x['asset_type'] for x in data['packages']]
        invalid_publishers = self.validate_publishers_package(data['publishers'], asset_types)
        invalid_loaders = self.validate_loaders_package(data['loaders'], asset_types)

        print "invalid_plugins --> {}".format(invalid_plugins)
        print "invalid_components --> {}".format(invalid_components)
        print "invalid_publishers --> {}".format(invalid_publishers)
        print "invalid_loaders --> {}".format(invalid_loaders)

        #self.cleanDefinitions(invalid_plugins, invalid_components, invalid_publishers, invalid_loaders)

    def validate_definitions(self, data):
        '''Find all schemas and validate all the definitions with the correcspondant schema'''
        for schema in data['schemas']:
            if schema['title'] == constants.LOADER_SCHEMA:
                self.validate_definition(schema, data['loaders'])
            elif schema['title'] == constants.PUBLISHER_SCHEMA:
                self.validate_definition(schema, data['publishers'])
            elif schema['title'] == constants.PACKAGE_SCHEMA:
                self.validate_definition(schema, data['packages'])
            else:
                self.logger.warning('The schema {} is not defined and can not be validated'.format(schema))


    def validate_definition(self, schema, data):
        '''Validate all the given definitions with the given schema'''
        for definition in data:
            try:
                _validate(schema, definition)
            except Exception as error:
                self.logger.debug(error)

    def validate_plugins(self, data):
        invalidPlugins = []
        for plugin in data:
            if not self._discover_plugin(plugin):
                self.logger.warning('Could not discover plugin {}'.format(plugin))
                invalidPlugins.append(plugin)
        return invalidPlugins or None

    def validate_components(self, components_data, package_compnents_data):
        '''
        validate if the publisher defines the correct components based on the
        package definition.
        '''
        invalidCompoenents=[]
        publisher_names = []
        for component in components_data:
            if component['name']:
                publisher_names.append(component['name'])

        # check if the mandatory components defined in the package definition
        # are available in the publisher definition.
        package_components_names = []
        for package_component in package_compnents_data:
            for package_component_name, optional in package_component.items():
                package_components_names.append(package_component_name)
                if optional:
                    continue
                if package_component_name not in publisher_names:
                    self.logger.warning('{} is not defined'.format(package_component_name))
                    invalidCompoenents.append(package_component)

        # check if the components defined in the publisher
        # are all available of the package definition
        for component in components_data:
            if component['name'] not in package_components_names:
                self.logger.warning('{} is not found in {}'.format(
                        component['name'], package_components_names))
                invalidCompoenents.append(component)

        return invalidCompoenents or None

    def validate_publishers_package(self, data, asset_types):
        '''validate if the publisher package is defined in the packages as asset_type'''
        invalidPublishers = []
        for publisher in data:
            if not publisher['package'] in asset_types:
                self.logger.warning(
                    'Publisher {} is not among the validated packages: {}'.format(
                        publisher, asset_types))
                invalidPublishers.append(publisher)

    def validate_loaders_package(self, data, asset_types):
        '''validate if the loader package is defined in the packages as asset_type'''
        invalidLoaders = []
        for loader in data:
            if not loader['package'] in asset_types:
                self.logger.warning(
                    'Loader {} is not among the validated packages: {}'.format(
                        loader, asset_types))
                invalidLoaders.append(loader)
        return invalidLoaders or None

    def cleanDefinitions(self):
        pass

    def _discover_plugin(self, plugin):
        '''Run *plugin*, *plugin_type*, with given *options*, *data* and *context*'''
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

        return plugin_result


class DefintionManager(object):
    '''class wrapper to contain all the definition managers.'''

    def __init__(self, event_manager, host):
        super(DefintionManager, self).__init__()

        self.session = event_manager.session

        self.definitions = BaseDefinitionManager(event_manager, host)

        self.json_definitions = self.definitions.result()
