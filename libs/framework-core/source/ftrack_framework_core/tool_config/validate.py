# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from ftrack_utils.framework.tool_config.read import get_plugins

logger = logging.getLogger(__name__)


def validate_tool_config_plugins(tool_configs, registered_plugin_names):
    '''
    Validates that all the plugins defined in the given *tool_configs* are
    registered in the given *registered_plugin_names*
    tool_configs : dictionary with tool-configs classified by type
    '''
    valid_configs = {}
    for config_type, configs in tool_configs.items():
        for tool_config in configs:
            tool_config_plugins = get_plugins(tool_config, names_only=True)
            is_valid = True
            for tool_config_plugin in tool_config_plugins:
                if tool_config_plugin not in registered_plugin_names:
                    logger.warning(
                        'Plugin {} from tool config {} is '
                        'not registered. Registered plugins {}'.format(
                            tool_config_plugin,
                            tool_config['name'],
                            registered_plugin_names,
                        )
                    )
                    is_valid = False
                    continue
            if not is_valid:
                logger.error(
                    'Tool config {} is not valid. It contains plugins that '
                    'have not been registered.'.format(tool_config['name'])
                )
                continue
            if config_type not in valid_configs:
                valid_configs[config_type] = []
            valid_configs[config_type].append(tool_config)

    return valid_configs
