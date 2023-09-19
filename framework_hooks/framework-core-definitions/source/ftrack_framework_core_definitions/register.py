# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging

from ftrack_utils.directories.scan_dir import fast_scandir
logger = logging.getLogger('ftrack_framework_definition.register')


# TODO: maybe use the utility here as well to align with widgets and plugins so
#  is easier for users to understand.
def register(event_manager):
    '''Register plugin to api_object.'''

    # We just need to pass the location of this file in order to register
    # definitions.
    current_dir = os.path.dirname(__file__)
    subfolders = fast_scandir(current_dir)
    return subfolders
