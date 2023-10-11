# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import copy

import python_jsonschema_objects as pjo

logger = logging.getLogger(__name__)


def _get_schema(schema_name, schemas):
    '''
    Returns the schema in the given *schemas* for the given *tool_config_type*

    *tool_config_type* : Type of the tool_config. (asset_manager, publisher...)

    *schemas* : List of schemas.
    '''
    for schema in schemas:
        if schema_name.lower() == schema['title'].lower():
            return schema
    return None


def validate_tool_config(schemas, tool_config):
    '''
    Validates the schema of the given *tool_config* from the given *schemas*
    using the _validate_jsonschema function of the jsonschema.validate library.

    *schemas* : List of schemas.

    *tool_config* : Tool config to be validated against the schema.
    '''
    # builder = pjo.ObjectBuilder(
    #     schemas[tool_config['validation_schema']], resolved=schemas
    # )
    # TODO: Double check if we get the ABCMeta error validating the definiition.
    #  If that occurs is because the pjo library gets corrupted when it executes
    #  build_classes during the augment
    # builder.validate(tool_config)

    # Returning Always true until above error is fixed.
    return True


def validate_tool_config_plugins(tool_configs, registered_plugin_names):
    '''
    Validates that all the plugins defined in the given *tool_configs* are
    registered in the given *registered_plugin_names*
    *tool_configs*: Should be a dictionary of toolConfigObjects
    '''
    # validate_plugins
    copy_data = copy.deepcopy(tool_configs)
    for tool_type, tool_config_list in tool_configs.items():
        for tool_config in tool_config_list:
            is_valid = True
            plugins = tool_config.get_all(category='plugin')
            for plugin in plugins:
                if plugin.plugin_name not in registered_plugin_names:
                    logger.warning(
                        'Plugin {} from tool config {} is '
                        'not registered. Registered plugins {}'.format(
                            plugin.plugin_name,
                            tool_config['tool_title'],
                            registered_plugin_names,
                        )
                    )
                    is_valid = False
                if not is_valid:
                    logger.warning(
                        'Tool config {} is not valid. It contains not '
                        'registered plugins.'.format(tool_config['tool_title'])
                    )
                    copy_data[tool_type].remove(tool_config)

    return copy_data
