# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

#import ftrack_api
import os
import logging
#from ftrack_framework_definition import Schema

logger = logging.getLogger('ftrack_framework_definition.register')

# TODO: As low priority task, improve schemas, re-use stuff like plugins,
#  and see how to make them simple.
# def register(api_object, **kw):
#     '''Register plugin to api_object.'''
#
#     # Validate that api_object is an instance of ftrack_api.Session. If not,
#     # assume that _register is being called from an incompatible API
#     # and return without doing anything.
#     print("in the first registry")
#     if not isinstance(api_object, ftrack_api.Session):
#         # Exit to avoid registering this plugin again.
#         return
#
#     schema = Schema(api_object)
#     current_dir = os.path.dirname(__file__)
#     schema.register(path=current_dir)
#     return current_dir

def temp_registry():
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register is being called from an incompatible API
    # and return without doing anything.
    print("in the first registry")
    current_dir = os.path.dirname(__file__)
    return current_dir
