# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import json
import fnmatch
import os
import logging
import copy
import python_jsonschema_objects as pjo

import ftrack_constants.framework as constants
from ftrack_framework_core.definition import definition_object

logger = logging.getLogger(__name__)


def discover_definitions_plugins(definitions, event_manager, host_types):
    '''
    Validates the given *data* against the correspondant plugin validator.
    Returns a validated data.

    *data* : Should be a validated and complete definitions and schemas coming from
    :func:`ftrack_connect_pipeline_definition.resource.definitions.register._register_definitions_callback`
    '''

    copy_data = copy.deepcopy(definitions)
    for tool_type, definitions in definitions.items():
        for definition in definitions:
            is_valid = _discover_plugins(definition, event_manager, host_types)
            if not is_valid:
                logger.warning(
                    'definition {} not valid for host types {}'.format(
                        definition['tool_title'], host_types
                    )
                )
                copy_data[tool_type].remove(definition)
    return copy_data


def _discover_plugins(definition, event_manager, host_types):
    '''
    Validates all the definitions in the given *definitions* definitions
    calling the :meth:`validate_context_plugins`,
    :meth:`validate_components_plugins`,
    :meth:`vaildate_finalizers_plugins`.

    Returns the invalid definition indices.

    *definitions* : List of definitions (opener, loader, publisher and so on).

    '''
    plugins = definition.get_all(category='plugin')
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

    *plugin* : Plugin definition, a dictionary with the plugin information.

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
                'plugin {} found for definition host_type {}'.format(
                    plugin_name, host_type
                )
            )
            break
        logger.warning(
            'plugin {} not found for definition host_type {}'.format(
                plugin_name, host_type
            )
        )

    return plugin_result


def filter_definitions_by_host(definitions, host_types):
    '''
    Filter the definitions in the given *data* by the given *host*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`discover_definitions`
    *host_types* : List of definition host to be filtered by.
    '''
    copy_data = copy.deepcopy(definitions)
    logger.debug('filtering definition for host_type: {}'.format(host_types))
    for tool_type, definitions in definitions.items():
        for definition in definitions:
            if str(definition.get('host_type')) not in host_types:
                logger.debug(
                    'Removing definition for host_type: {}'.format(
                        definition.get('host_type')
                    )
                )
                copy_data[tool_type].remove(definition)

    return copy_data


def discover_definitions(definition_paths):
    '''
    Collect all definitions from the given
    *definition_paths*

    *definition_paths* : Directory path to look for the definitions.
    '''
    definitions = {}
    for lookup_dir in definition_paths:
        collected_files = _collect_json(lookup_dir)
        for definition in collected_files:
            if not definition.get('tool_type'):
                logger.error(
                    "Not registring definition as is missing "
                    "tool_type key. Directory: {}, definition: {}".format(
                        lookup_dir, definition
                    )
                )
                continue
            if definition['tool_type'] not in definitions.keys():
                definitions[definition['tool_type']] = []
            definitions[definition['tool_type']].append(definition)
        logger.debug(
            'Found {} in path: {}'.format(len(collected_files), lookup_dir)
        )

    return definitions


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
            'Found {} {} in path: {}'.format(
                len(collected_files), constants.definition.SCHEMA, lookup_dir
            )
        )

    return schemas


def _collect_json(source_path):
    '''
    Return a json encoded list of all the json files discovered in the given
    *source_path*.
    '''
    logger.debug('looking for definitions in : {}'.format(source_path))

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
    # TODO: double check this: We have a problem with the definitions augment,
    #  need to doublecheck what is going on, if we resolve schemas before
    #  augmenting the definitions it doesn’t work.
    return schemas
    # schemas = [
    #     JsonRef.replace_refs(schema) for schema in schemas
    # ]
    # return schemas


def _augment_definition(definition, schemas):
    '''
    Augments the given *definition* with the values from the validation_schema
    key that should be in given *schemas*
    '''
    # Pick the schema to validate with from the definition, validation_schema
    # key
    validation_schema_title = definition.get('validation_schema')
    if not validation_schema_title:
        logger.error(
            "Given definition should have validation_schema key to know which "
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
    # Initialize the main class with the given *definition* json as kwargs.
    # Example: ToolSchema(tool_title='File Publisher'...)
    klass = ObjectBuilder(**definition)
    # Now will validate and augment the data. Will return the final schema with
    # the modified values
    serialised_data = klass.serialize()
    return json.loads(serialised_data)


def augment_definition(definitions, schemas):
    '''
    Validates and augments the definitions and the schemas from the given *data*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`discover_definitions`
    '''
    copy_definitions = copy.deepcopy(definitions)

    for tool_type, definitions in definitions.items():
        for definition in definitions:
            # Remove the definition from the list, so we will replace it for the
            # augmented one
            copy_definitions[tool_type].remove(definition)
            try:
                augmented_valid_data = _augment_definition(definition, schemas)
            except Exception as error:
                logger.error(
                    '{} does not match any schema. {}'.format(
                        definition.get('tool_title'), str(error)
                    )
                )
                continue
            copy_definitions[tool_type].append(
                definition_object.DefinitionObject(augmented_valid_data)
            )
            # Convert lists to DefinitionList
        copy_definitions[tool_type] = definition_object.DefinitionList(
            copy_definitions[tool_type]
        )

    return copy_definitions
