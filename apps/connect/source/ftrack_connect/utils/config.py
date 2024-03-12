# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import logging

import platformdirs

from ftrack_utils.yaml import read_yaml_file, write_yaml_file

logger = logging.getLogger(__name__)


def get_connect_config_file_path():
    '''Return Path of the ftrack_connect.yaml file'''
    prefs_file = os.path.join(
        platformdirs.user_data_dir('ftrack-connect', 'ftrack'),
        'ftrack_connect.yaml',
    )
    return prefs_file


def get_connect_config():
    '''Return the content of the ftrack_connect.yaml file'''
    prefs_file = get_connect_config_file_path()

    return read_yaml_file(prefs_file)


def write_connect_config_file_path(content):
    '''Write the content to the ftrack_connect.yaml file'''
    prefs_file = get_connect_config_file_path()

    return write_yaml_file(prefs_file, content)
