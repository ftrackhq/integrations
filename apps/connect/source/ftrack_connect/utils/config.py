# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import logging

import platformdirs

from ftrack_utils.yaml import read_yaml_file, write_yaml_file

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

    return read_yaml_file(config_file)


def write_connect_config_file_path(content):
    '''Write the content to the ftrack_connect.yaml file'''
    config_file = get_connect_config_file_path()

    return write_yaml_file(config_file, content)
