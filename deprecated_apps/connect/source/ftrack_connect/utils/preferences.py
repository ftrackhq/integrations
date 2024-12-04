# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import logging

import platformdirs

from ftrack_utils.json import read_json_file, write_json_file

logger = logging.getLogger(__name__)


def get_connect_prefs_file_path():
    '''Return Path of the prefs.json file'''
    prefs_file = os.path.join(
        platformdirs.user_data_dir('ftrack-connect', 'ftrack'),
        'prefs.json',
    )
    return prefs_file


def get_connect_preferences():
    '''Return the content of the prefs.json file'''
    prefs_file = get_connect_prefs_file_path()

    return read_json_file(prefs_file)


def write_connect_prefs_file_path(content):
    '''Write the content of of the prefs.json file'''
    prefs_file = get_connect_prefs_file_path()

    return write_json_file(prefs_file, content)
