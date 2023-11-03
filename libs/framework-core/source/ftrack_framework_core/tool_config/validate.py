# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import copy

import python_jsonschema_objects as pjo

logger = logging.getLogger(__name__)


def validate_tool_config_plugins(tool_configs, registered_plugin_names):
    '''
    Validates that all the plugins defined in the given *tool_configs* are
    registered in the given *registered_plugin_names*
    *tool_configs*: Should be a dictionary of toolConfigObjects
    '''
    # TODO: review this once task to evaluate toolConfigObject is in place.
    return tool_configs
    # validate_plugins
    # copy_data = copy.deepcopy(tool_configs)
    # for tool_type, tool_config_list in tool_configs.items():
    #     for tool_config in tool_config_list:
    #         is_valid = True
    #         plugins = tool_config.get_all(category='plugin')
    #         for plugin in plugins:
    #             if plugin.plugin_name not in registered_plugin_names:
    #                 logger.warning(
    #                     'Plugin {} from tool config {} is '
    #                     'not registered. Registered plugins {}'.format(
    #                         plugin.plugin_name,
    #                         tool_config['tool_title'],
    #                         registered_plugin_names,
    #                     )
    #                 )
    #                 is_valid = False
    #             if not is_valid:
    #                 logger.warning(
    #                     'Tool config {} is not valid. It contains plugins that '
    #                     'have not been registered.'.format(
    #                         tool_config['tool_title']
    #                     )
    #                 )
    #                 copy_data[tool_type].remove(tool_config)
    #
    # return copy_data
