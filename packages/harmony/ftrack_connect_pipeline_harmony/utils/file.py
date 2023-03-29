# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import threading
from functools import wraps
import logging

from ftrack_connect_pipeline.utils import (
    get_save_path,
)
from ftrack_connect_pipeline_harmony.constants import asset as asset_const

logger = logging.getLogger(__name__)


### FILE OPERATIONS ###


def open_file(path, options=None):
    '''Native open file function '''
    # return cmds.file(path, o=True, f=True)
    pass


def import_file(path, options=None):
    '''Native import file function '''
    # return cmds.file(path, o=True, f=True)
    pass


def save_file(save_path, context_id=None, session=None, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on latest version
    in ftrack.'''

    # # Max has no concept of renaming a scene, always save
    # save = True
    #
    # if save_path is None:
    #     if context_id is not None and session is not None:
    #         # Attempt to find out based on context
    #         save_path, message = get_save_path(
    #             context_id, session, extension='.max', temp=temp
    #         )
    #
    #         if save_path is None:
    #             return False, message
    #     else:
    #         return (
    #             False,
    #             'No context and/or session provided to generate save path',
    #         )
    #
    # if save:
    #     rt.savemaxFile(save_path, useNewFile=True)
    #     message = 'Saved Max scene @ "{}"'.format(save_path)
    # else:
    #     raise Exception('Max scene rename not supported')
    #
    # result = save_path
    #
    # return result, message
    pass


### REFERENCES ###
# Follow this link for more reference commands in max:
# https://help.autodesk.com/view/3DSMAX/2016/ENU/?guid=__files_GUID_090B28AB_5710_45BB_B324_8B6FD131A3C8_htm


def reference_file(path, options=None):
    '''Native reference file function '''
    # return cmds.file(path, o=True, f=True)
    pass
