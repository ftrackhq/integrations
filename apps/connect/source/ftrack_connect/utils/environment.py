# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os


def get_connect_extensions_path_from_environment():
    '''Extract list of extension paths from the OS environment.'''

    environment_variable = 'FTRACK_CONNECT_EXTENSIONS_PATH'
    paths = os.environ.get(environment_variable, '')
    return paths.split(os.pathsep) if paths else []
