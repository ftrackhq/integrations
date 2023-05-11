# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import maya.cmds as cmds
import maya.mel as mm

from ftrack_connect_pipeline.utils import (
    get_save_path,
)


def open_file(path, options):
    '''Open file at *path* with *options*.'''
    return cmds.file(path, o=True, f=True)


def import_file(path, options):
    '''Import file at *path* with *options*.'''
    return cmds.file(path, i=True, **options)


def reference_file(path, options):
    '''Reference file at *path* with *options*.'''
    return cmds.file(path, r=True, **options)


def save_file(context_id, session, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on latest version
    in ftrack.'''

    save_path, message = get_save_path(
        context_id, session, extension='.mb', temp=temp
    )

    if save_path is None:
        return False, message

    # Save Maya scene to this path
    cmds.file(rename=save_path)
    if save:
        cmds.file(save=True)
        message = 'Saved Maya scene @ "{}"'.format(save_path)
    else:
        message = 'Renamed Maya scene @ "{}"'.format(save_path)
    if not temp:
        # Add to recent files
        mm.eval("source addRecentFile;")
        mm.eval(
            'addRecentFile("{}.mb","{}");'.format(
                save_path.replace('\\', '/'), 'mayaBinary'
            )
        )

    result = save_path

    return result, message
