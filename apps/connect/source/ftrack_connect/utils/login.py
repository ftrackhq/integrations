# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import os.path
import platformdirs
import json
import logging


logger = logging.getLogger('ftrack_connect.ui.config')


def get_config_file_path():
    '''Return config file path.'''
    config_file = os.path.join(
        platformdirs.user_data_dir('ftrack-connect', 'ftrack'), 'config.json'
    )

    return config_file


def read_json_config():
    '''Return json config from disk storage.'''
    config_file = get_config_file_path()
    config = None

    if os.path.isfile(config_file):
        logger.debug(u'Reading config from {0}'.format(config_file))

        with open(config_file, 'r') as file:
            try:
                config = json.load(file)
            except Exception:
                logger.exception(
                    u'Exception reading json config in {0}.'.format(
                        config_file
                    )
                )

    return config


def write_json_config(config):
    '''Write *config* as json file.'''
    config_file = get_config_file_path()

    # Create folder if it does not exist.
    folder = os.path.dirname(config_file)
    if not os.path.isdir(folder):
        os.makedirs(folder)

    with open(config_file, 'w') as file:
        json.dump(config, file)
