# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging

logger = logging.getLogger('ftrack_framework_schemas.register')

# TODO: maybe use the utility here as well to align with widgets and plugins so
#  is easier for users to understand.
def register(event_manager):
    '''Register plugin to api_object.'''

    # We just need to pass the location of this file in order to register
    # schemas.
    current_dir = os.path.dirname(__file__)
    return current_dir
