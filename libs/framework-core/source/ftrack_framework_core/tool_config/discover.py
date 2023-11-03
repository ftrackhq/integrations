# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import copy
import yaml

logger = logging.getLogger(__name__)


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
    loaded_files = load_yaml_files(tool_config_paths)
    for tool_config in loaded_files:
        if not tool_config.get('config_type'):
            logger.error(
                "Not registering tool config as is missing "
                "config_type key. Tool_config: {}".format(tool_config)
            )
            continue
        if tool_config['config_type'] not in tool_configs.keys():
            tool_configs[tool_config['config_type']] = []
        tool_configs[tool_config['config_type']].append(tool_config)

    return tool_configs


def load_yaml_files(file_list):
    '''
    Generate data registry files for all compatible framework .yaml files in
    the given *file_list*
    '''
    loaded_yaml = []
    for _file in file_list:
        with open(_file, 'r') as yaml_file:
            try:
                yaml_content = yaml.safe_load(yaml_file)
                loaded_yaml.append(yaml_content)
            except yaml.YAMLError as exc:
                # Log an error if the yaml file is invalid.
                logger.error(
                    "Invalid .yaml file\nFile: {}\nError: {}".format(
                        _file, exc
                    )
                )
                continue
    return loaded_yaml
