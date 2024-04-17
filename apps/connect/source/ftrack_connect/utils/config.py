# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import glob
import logging

import platformdirs

from ftrack_utils.yaml import (
    read_yaml_file,
    write_yaml_file,
    substitute_placeholders,
)

logger = logging.getLogger(__name__)


def get_default_config_directory():
    return platformdirs.user_data_dir('ftrack-connect', 'ftrack')


def get_connect_config_path():
    '''Return Path of the ftrack_connect.yaml file'''
    config_path = os.getenv(
        'FTRACK_CONNECT_CONFIG_PATH', get_default_config_directory()
    )
    return config_path


def get_connect_config():
    '''Return the content of the ftrack_connect.yaml file'''
    config_path = get_connect_config_path()
    yaml_files = glob.glob(os.path.join(config_path, '*.yaml'))

    found_config = None
    for yaml_file in yaml_files:
        yaml_content = read_yaml_file(yaml_file)
        if yaml_content.get('type') != 'connect_config':
            logger.warning(
                "Ignoring file {yaml_file} as is not tagged as connect_config type"
            )
            continue
        try:
            found_config = substitute_placeholders(yaml_content, yaml_content)
        except Exception as e:
            raise Exception(
                f"Error found on parsing connect config file {yaml_file}. Error: {e}"
            )
        break

    return found_config


def write_connect_config_file_path(content):
    '''Write the content to the ftrack_connect.yaml file'''
    config_path = get_connect_config_path()
    config_file = os.path.join(config_path, 'ftrack_connect.yaml')

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
