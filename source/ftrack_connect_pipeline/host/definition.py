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


def filter_by_host(json_data, host):
    json_copy = copy.deepcopy(json_data)
    for definition_name, values in json_data.items():
        for definition in values:
            if definition.get('host') and definition.get('host') != host:
                idx = json_copy[definition_name].index(definition)
                json_copy[definition_name].pop(idx)
    return json_copy


def parse_dictonary(self, data, value_filter, new_list):
    if isinstance(data, dict):
        if data.get('type') == value_filter:
            new_list.append(data)
        else:
            for key, value in data.items():
                parse_dictonary(value, value_filter, new_list)
    if isinstance(data, list):
        for item in data:
            parse_dictonary(item, value_filter, new_list)


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

        result = filter_by_host(raw_result, self.host)

        if not result:
            return

        validated_result = self.validate_result(result)

        # validate here

        self.__registry = validated_result

        handle_event = partial(provide_host_information, self.hostid, validated_result)
        self.session.event_hub.subscribe(
            'topic={}'.format(
                constants.PIPELINE_DISCOVER_HOST
            ),
            handle_event
        )
        self.logger.info('host {} ready.'.format(self.hostid))

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

    def validate_result(self, data):

        self.validate_definitions(data)

        # invalid_publishers_idxs = self.validate_publishers_plugins(data['publishers'])
        # for idx in invalid_publishers_idxs:
        #     data['publishers'].pop(idx)
        #
        # invalid_loaders_idxs = self.validate_loaders_plugins(data['loaders'])
        # for idx in invalid_loaders_idxs:
        #     data['loaders'].pop(idx)
        #
        # invalid_publishers_idxs = self.validate_publishers_components(data['publishers'])
        # for idx in invalid_publishers_idxs:
        #     data['publishers'].pop(idx)

        # components_l = []
        # self.parse_dictonary(data, 'component', components_l)
        # package_components_l = []
        # self.parse_dictonary(data, 'package_component', package_components_l)
        # invalid_components = self.validate_components(components_l, package_components_l)
        # #self.clear_invalid_components(data, invalid_components)

        '''asset_types = [x['asset_type'] for x in data['packages']]
        invalid_publishers = self.validate_publishers_package(data['publishers'], asset_types)
        invalid_loaders = self.validate_loaders_package(data['loaders'], asset_types)'''

        return data

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
        print plugin_result

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
