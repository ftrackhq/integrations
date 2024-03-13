# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import os.path
import platformdirs
import json
import logging


logger = logging.getLogger('ftrack_connect.utils.loging')


def get_login_file_path():
    '''Return config file path.'''
    login_file = os.path.join(
        platformdirs.user_data_dir('ftrack-connect', 'ftrack'), 'login.json'
    )

    return login_file


def read_json_login():
    '''Return json config from disk storage.'''
    login_file = get_login_file_path()
    login = None

    if os.path.isfile(login_file):
        logger.debug(u'Reading login from {0}'.format(login_file))

        with open(login_file, 'r') as file:
            try:
                login = json.load(file)
            except Exception:
                logger.exception(
                    u'Exception reading json config in {0}.'.format(login_file)
                )

    return login


def write_json_login(config):
    '''Write *config* as json file.'''
    login_file = get_login_file_path()

    # Create folder if it does not exist.
    folder = os.path.dirname(login_file)
    if not os.path.isdir(folder):
        os.makedirs(folder)

    with open(login_file, 'w') as file:
        json.dump(config, file)
