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
    for entry in constants.definition.DEFINITION_TYPES:
        for definition in definitions[entry]:
            is_valid = _discover_plugins(definition, event_manager, host_types)
            if not is_valid:
                logger.warning(
                    'definition {} not valid for host types {}'.format(
                        definition['name'], host_types
                    )
                )
                copy_data[entry].remove(definition)
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
    plugin_name = plugin['plugin']
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
    for entry in constants.definition.DEFINITION_TYPES:
        for definition in definitions[entry]:
            # TODO: host_type should be replaced by a constant.
            if str(definition.get('host_type')) not in host_types:
                logger.debug(
                    'Removing definition for host_type: {}'.format(
                        definition.get('host_type')
                    )
                )
                copy_data[entry].remove(definition)

    return copy_data


def discover_definitions(definition_paths):
    '''
    Collect all the schemas and definitions from the given
    *definition_paths*

    *definition_paths* : Directory path to look for the definitions.
    '''
    definitions = {}
    for lookup_dir in definition_paths:
        for file_type in constants.definition.DEFINITION_TYPES:
            if file_type not in definitions.keys():
                definitions[file_type] = []
            search_path = os.path.join(lookup_dir, file_type)
            collected_files = _collect_json(search_path)
            definitions[file_type].extend(collected_files)
            logger.debug(
                'Found {} {} in path: {}'.format(
                    len(collected_files), file_type, search_path
                )
            )

    return definitions


def discover_schemas(schema_paths):
    '''
    Collect all the schemas and definitions from the given
    *definition_paths*

    *definition_paths* : Directory path to look for the definitions.
    '''
    schemas = []
    for lookup_dir in schema_paths:
        search_path = os.path.join(lookup_dir, constants.definition.SCHEMA)
        collected_files = _collect_json(search_path)
        schemas.extend(collected_files)
        logger.debug(
            'Found {} {} in path: {}'.format(
                len(collected_files), constants.definition.SCHEMA, search_path
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
    Resolves the refs of the schemas in the given *data*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`discover_definitions`
    '''
    # TODO: double check this: We have a problem with the definitions augment,
    #  need to doublecheck what is going on, if we resolve schemas before
    #  augmenting the definitions it doesn’t work.
    return schemas
    # schemas = [
    #     JsonRef.replace_refs(schema) for schema in schemas
    # ]
    # return schemas


def _augment_definition(schema, definition, type):
    '''
    Augments the given *definition* of the given *type* with the
    given *schema*
    '''
    # TODO: double check if there is a more comprehensive way to augment definitions
    builder = pjo.ObjectBuilder(schema)
    ns = builder.build_classes(standardize_names=False)
    ObjectBuilder = getattr(ns, type.capitalize())
    klass = ObjectBuilder(**definition)
    serialised_data = klass.serialize()
    return json.loads(serialised_data)


def augment_definition(definitions, schemas, session):
    '''
    Validates and augments the definitions and the schemas from the given *data*

    *data* : Dictionary of json definitions and schemas generated at
    :func:`discover_definitions`
    '''
    copy_definitions = copy.deepcopy(definitions)
    valid_assets_types = [
        type['short']
        for type in session.query('select short from AssetType').all()
    ]

    # validate schema
    for schema in schemas:
        for entry in constants.definition.DEFINITION_TYPES:
            if schema['title'].lower() == entry:
                for definition in definitions[entry]:
                    copy_definitions[entry].remove(definition)
                    if schema['title'].lower() not in [
                        constants.definition.ASSET_MANAGER,
                        constants.definition.RESOLVER,
                    ]:
                        if (
                            definition.get('asset_type')
                            not in valid_assets_types
                        ):
                            logger.error(
                                'Definition {} does use a non existing'
                                ' asset type: {}'.format(
                                    definition['name'],
                                    definition.get('asset_type'),
                                )
                            )
                            continue

                    try:
                        augmented_valid_data = _augment_definition(
                            schema, definition, entry
                        )
                    except Exception as error:
                        logger.error(
                            '{} {} does not match any schema. {}'.format(
                                entry, definition['name'], str(error)
                            )
                        )

                        continue
                    copy_definitions[entry].append(
                        definition_object.DefinitionObject(
                            augmented_valid_data
                        )
                    )
                # Convert lists to DefinitionList
                copy_definitions[entry] = definition_object.DefinitionList(
                    copy_definitions[entry]
                )

    return copy_definitions
