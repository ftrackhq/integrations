# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import os.path
import platformdirs
import json
import logging


logger = logging.getLogger('ftrack_connect.utils.credentials')


def get_credentials_file_path():
    '''Return config file path.'''
    credentials_file = os.path.join(
        platformdirs.user_data_dir('ftrack-connect', 'ftrack'),
        'credentials.json',
    )

    return credentials_file


def load_credentials():
    '''Return json config from disk storage.'''
    credentials_file = get_credentials_file_path()
    credentials = None

    if os.path.isfile(credentials_file):
        logger.debug(u'Reading credentials from {0}'.format(credentials_file))

        with open(credentials_file, 'r') as file:
            try:
                credentials = json.load(file)
            except Exception:
                logger.exception(
                    u'Exception reading json credentials in {0}.'.format(
                        credentials_file
                    )
                )

    return credentials


def store_credentials(config):
    '''Write *config* as json file.'''
    credentials_file = get_credentials_file_path()

    # Create folder if it does not exist.
    folder = os.path.dirname(credentials_file)
    if not os.path.isdir(folder):
        os.makedirs(folder)

    with open(credentials_file, 'w') as file:
        json.dump(config, file)
