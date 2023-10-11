# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging

from ftrack_utils.directories.scan_dir import fast_scandir

logger = logging.getLogger('ftrack_framework_schemas.register')

PACKAGE_TYPE = "schema"


def register():
    '''Register plugin to api_object.'''

    # We just need to pass the location of this file in order to register
    # schemas.
    current_dir = os.path.dirname(__file__)
    subfolders = fast_scandir(current_dir)
    return subfolders
