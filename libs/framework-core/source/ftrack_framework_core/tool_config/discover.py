# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import json
import fnmatch
import os
import logging
import copy
import python_jsonschema_objects as pjo

import ftrack_constants.framework as constants
from ftrack_framework_core.tool_config import tool_config_object

logger = logging.getLogger(__name__)


def discover_tool_configs_plugins(tool_configs, event_manager, host_types):
    '''
    Validates the given *data* against the correspondant plugin validator.
    Returns a validated data.

    *data* : Should be a validated and complete tool_configs and schemas coming from
    :func:`ftrack_connect_pipeline_tool_config.resource.tool_configs.register._register_tool_configs_callback`
    '''

    copy_data = copy.deepcopy(tool_configs)
    for tool_type, tool_configs in tool_configs.items():
        for tool_config in tool_configs:
            is_valid = _discover_plugins(
                tool_config, event_manager, host_types
            )
            if not is_valid:
                logger.warning(
                    'tool_config {} not valid for host types {}'.format(
                        tool_config['tool_title'], host_types
                    )
                )
                copy_data[tool_type].remove(tool_config)
    return copy_data


def _discover_plugins(tool_config, event_manager, host_types):
    '''
    Validates all the tool_configs in the given *tool_configs* tool_configs
    calling the :meth:`validate_context_plugins`,
    :meth:`validate_components_plugins`,
    :meth:`vaildate_finalizers_plugins`.

    Returns the invalid tool_config indices.

    *tool_configs* : List of tool_configs (opener, loader, publisher and so on).

    '''
    plugins = tool_config.get_all(category='plugin')
    invalid_plugins = []
    for plugin in plugins:
        if not _discover_plugin(event_manager, host_types, plugin):
            invalid_plugins.append(plugin)
    if invalid_plugins:
        return False
    return True


def _discover_plugin(event_manager, host_types, plugin):
    '''
    Publish an event with the topic
    :py:const:`~ftrack_framework_core.constants.DISCOVER_PLUGIN_TOPIC`
    with the given *plugin* name and *plugin_type* as data to check that the
    pluging can be discovered with no issues.

    Returns the result of the event.

    *plugin* : Plugin tool_config, a dictionary with the plugin information.

    *plugin_type* : Type of plugin
    '''
    plugin_name = plugin['plugin_name']
    plugin_result = {}

    for host_type in reversed(host_types):
        plugin_result = event_manager.publish.discover_plugin(
            host_type,
            plugin_name,
        )

        if plugin_result:
            logger.debug(
                'plugin {} found for tool_config host_type {}'.format(
                    plugin_name, host_type
                )
            )
            break
        logger.warning(
            'plugin {} not found for tool_config host_type {}'.format(
                plugin_name, host_type
            )
        )

    return plugin_result


def filter_tool_configs_by_host(tool_configs, host_types):
    '''
    Filter the tool_configs in the given *data* by the given *host*

    *data* : Dictionary of json tool_configs and schemas generated at
    :func:`discover_tool_configs`
    *host_types* : List of tool_config host to be filtered by.
    '''
    copy_data = copy.deepcopy(tool_configs)
    logger.debug('filtering tool_config for host_type: {}'.format(host_types))
    for tool_type, tool_configs in tool_configs.items():
        for tool_config in tool_configs:
            if str(tool_config.get('host_type')) not in host_types:
                logger.debug(
                    'Removing tool_config for host_type: {}'.format(
                        tool_config.get('host_type')
                    )
                )
                copy_data[tool_type].remove(tool_config)

    return copy_data


def discover_tool_configs(tool_config_paths):
    '''
    Collect all tool_configs from the given
    *tool_config_paths*

    *tool_config_paths* : Directory path to look for the tool_configs.
    '''
    tool_configs = {}
    for lookup_dir in tool_config_paths:
        collected_files = _collect_json(lookup_dir)
        for tool_config in collected_files:
            if not tool_config.get('tool_type'):
                logger.error(
                    "Not registring tool_config as is missing "
                    "tool_type key. Directory: {}, tool_config: {}".format(
                        lookup_dir, tool_config
                    )
                )
                continue
            if tool_config['tool_type'] not in tool_configs.keys():
                tool_configs[tool_config['tool_type']] = []
            tool_configs[tool_config['tool_type']].append(tool_config)
        logger.debug(
            'Found {} in path: {}'.format(len(collected_files), lookup_dir)
        )

    return tool_configs


def discover_schemas(schema_paths):
    '''
    Collect all the schemas from the given
    *schema_paths*

    *schema_paths* : Directory path to look for the schemas.
    '''
    schemas = {}
    for lookup_dir in schema_paths:
        collected_files = _collect_json(lookup_dir)
        for json_schema in collected_files:
            schemas[json_schema['title']] = json_schema
        logger.debug(
            'Found {} schema(s) in path: {}'.format(
                len(collected_files), lookup_dir
            )
        )

    return schemas


def _collect_json(source_path):
    '''
    Return a json encoded list of all the json files discovered in the given
    *source_path*.
    '''
    logger.debug('looking for tool_configs in : {}'.format(source_path))

    json_files = []
    for root, dirnames, filenames in os.walk(source_path):
        for filename in fnmatch.filter(filenames, '*.json'):
            json_files.append(os.path.join(root, filename))

    loaded_jsons = []
    for json_file in json_files:
        data_store = None
        with open(json_file, 'r') as _file:
            try:
                data_store = json.load(_file)
            except Exception as error:
                logger.error(
                    "{0} could not be registered, reason: {1}".format(
                        _file, str(error)
                    )
                )
        if data_store:
            loaded_jsons.append(data_store)

    return loaded_jsons


# TODO: remove this function as its not used anymore
def resolve_schemas(schemas):
    '''
    Resolves the refs of the schemas in the given *schemas*

    *schemas* : Dictionary of json schemas.
    '''
    # TODO: double check this: We have a problem with the tool_configs augment,
    #  need to doublecheck what is going on, if we resolve schemas before
    #  augmenting the tool_configs it doesn’t work.
    return schemas
    # schemas = [
    #     JsonRef.replace_refs(schema) for schema in schemas
    # ]
    # return schemas


def _augment_tool_config(tool_config, schemas):
    '''
    Augments the given *tool_config* with the values from the validation_schema
    key that should be in given *schemas*
    '''
    # Pick the schema to validate with from the tool_config, validation_schema
    # key
    validation_schema_title = tool_config.get('validation_schema')
    if not validation_schema_title:
        logger.error(
            "Given tool_config should have validation_schema key to know which "
            "schema validate and augment from."
        )
    # Convert the current schema to pjo objectBuilder and resolve references
    # with the other schemas.
    builder = pjo.ObjectBuilder(
        schemas[validation_schema_title], resolved=schemas
    )
    # Build the object to obtain a pythonic object from the schema.ns will
    # contain things like ns.Publisher ns.title, etc...
    ns = builder.build_classes(standardize_names=False)
    # Pick the main class from the ns given on *type*. example Publisher
    ObjectBuilder = getattr(ns, validation_schema_title)
    # Initialize the main class with the given *tool_config* json as kwargs.
    # Example: ToolSchema(tool_title='File Publisher'...)
    klass = ObjectBuilder(**tool_config)
    # Now will validate and augment the data. Will return the final schema with
    # the modified values
    serialised_data = klass.serialize()
    return json.loads(serialised_data)


def augment_tool_config(tool_configs, schemas):
    '''
    Validates and augments the tool_configs and the schemas from the given *data*

    *data* : Dictionary of json tool_configs and schemas generated at
    :func:`discover_tool_configs`
    '''
    copy_tool_configs = copy.deepcopy(tool_configs)

    for tool_type, tool_configs in tool_configs.items():
        for tool_config in tool_configs:
            # Remove the tool_config from the list, so we will replace it for the
            # augmented one
            copy_tool_configs[tool_type].remove(tool_config)
            try:
                augmented_valid_data = _augment_tool_config(
                    tool_config, schemas
                )
            except Exception as error:
                logger.error(
                    '{} does not match any schema. {}'.format(
                        tool_config.get('tool_title'), str(error)
                    )
                )
                continue
            copy_tool_configs[tool_type].append(
                tool_config_object.ToolConfigObject(augmented_valid_data)
            )
            # Convert lists to Tool_configList
        copy_tool_configs[tool_type] = tool_config_object.Tool_configList(
            copy_tool_configs[tool_type]
        )

    return copy_tool_configs
