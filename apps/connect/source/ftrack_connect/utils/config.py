# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import logging

import platformdirs

from ftrack_utils.yaml import (
    read_yaml_file,
    write_yaml_file,
    substitute_placeholders,
)

logger = logging.getLogger(__name__)


def get_default_config_directory():
    return platformdirs.user_data_dir('ftrack-connect-plugins', 'ftrack')


def get_connect_config_file_path():
    '''Return Path of the ftrack_connect.yaml file'''
    config_path = os.getenv(
        'FTRACK_CONNECT_CONFIG_PATH', get_default_config_directory()
    )
    config_file = os.path.join(
        config_path,
        'ftrack_connect.yaml',
    )
    return config_file


def get_connect_config():
    '''Return the content of the ftrack_connect.yaml file'''
    config_file = get_connect_config_file_path()
    yaml_content = read_yaml_file(config_file)

    return substitute_placeholders(yaml_content, yaml_content)


def write_connect_config_file_path(content):
    '''Write the content to the ftrack_connect.yaml file'''
    config_file = get_connect_config_file_path()

    return write_yaml_file(config_file, content)


def verify_connect_config(connect_config, default_values):
    '''
    Make sure the given *connect_config* has all keys defined on the
    *default_values*, if not, set the default values on it.
    '''
    for k, v in default_values.items():
        if k not in connect_config.keys():
            logger.warning(
                f"Missing default {k} key on Connect_config file, setting it up with the default value: {v}"
            )
            connect_config[k] = v
    return connect_config
