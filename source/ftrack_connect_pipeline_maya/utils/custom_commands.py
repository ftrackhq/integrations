# :coding: utf-8
# :copyright: Copyright (c) 2022 ftrack
import logging
import os
import threading
from functools import wraps

from Qt import QtWidgets, QtCompat

import maya.OpenMayaUI as OpenMayaUI

import maya.utils as maya_utils
import maya.cmds as cmds
import maya.mel as mm

from ftrack_connect_pipeline.utils import (
    get_save_path,
)
from ftrack_connect_pipeline_maya.constants import asset as asset_const

logger = logging.getLogger(__name__)


def run_in_main_thread(f):
    '''Make sure a function runs in the main Maya thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            return maya_utils.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated


def get_current_scene_objects():
    return set(cmds.ls(l=True))


def get_ftrack_nodes():
    return cmds.ls(type=asset_const.FTRACK_PLUGIN_TYPE)


def open_file(path, options):
    return cmds.file(path, o=True, f=True)


def import_file(path, options):
    return cmds.file(path, i=True, **options)


def reference_file(path, options):
    return cmds.file(path, r=True, **options)


def remove_reference_node(referenceNode):
    return cmds.file(rfn=referenceNode, rr=True)


def getReferenceNode(assetLink):
    '''Return the references dcc_objects for the given *assetLink*'''
    res = ''
    try:
        res = cmds.referenceQuery(assetLink, referenceNode=True)
    except:
        children = cmds.listRelatives(assetLink, children=True)

        if children:
            for child in children:
                try:
                    res = cmds.referenceQuery(child, referenceNode=True)
                    break

                except:
                    pass
        else:
            return None
    if res == '':
        print('Could not find reference dcc_object')
        return None
    else:
        return res


def get_main_window():
    """Return the QMainWindow for the main Maya window."""
    winptr = OpenMayaUI.MQtUtil.mainWindow()
    if winptr is None:
        raise RuntimeError('No Maya window found.')
    window = QtCompat.wrapInstance(int(winptr))
    assert isinstance(window, QtWidgets.QMainWindow)
    return window


def init_maya(host, from_context=False):
    '''
    Initialise timeline in Nuke based on shot/asset build settings.

    :param session:
    :param from_context: If True, the timeline data should be fetched from current context instead of environment variables.
    :return:
    '''
    fps = None
    if from_context:
        context = host.session.query(
            'Context where id={}'.format(host.context_id)
        ).first()
        if context is None:
            logger.error(
                'Cannot initialize Maya timeline - no such context: {}'.format(
                    host.context_id
                )
            )
            return
        shot = None
        if context.entity_type == 'Shot':
            shot = context
        elif context.entity_type == 'Task':
            parent = context['parent']
            if parent.entity_type == 'Shot':
                shot = parent
        if not shot:
            logger.warning(
                'Cannot initialize Maya timeline - no shot related to context: {}'.format(
                    host.context_id
                )
            )
            return
        elif (
            not 'fstart' in shot['custom_attributes']
            or not 'fend' in shot['custom_attributes']
        ):
            logger.warning(
                'Cannot initialize Maya timeline - no fstart or fend shot custom attributes available'.format()
            )
            return
        start_frame = int(shot['custom_attributes']['fstart'])
        end_frame = int(shot['custom_attributes']['fend'])
        if 'fps' in shot['custom_attributes']:
            fps = float(shot['custom_attributes']['fps'])
    else:
        # Set default values from environments.
        start_frame = os.environ.get('FS', 0)
        end_frame = os.environ.get('FE', 100)
        if 'FPS' in os.environ:
            fps = float(os.environ['FPS'])

    logger.info('Setting start frame : {}'.format(start_frame))
    cmds.setAttr('defaultRenderGlobals.startFrame', start_frame)

    logger.info('Setting end frame : {}'.format(end_frame))
    cmds.setAttr('defaultRenderGlobals.endFrame', end_frame)

    cmds.playbackOptions(min=start_frame, max=end_frame)

    if fps is not None:
        fps_unit = "film"
        if fps == 15:
            fps_unit = "game"
        elif fps == 25:
            fps_unit = "pal"
        elif fps == 30:
            fps_unit = "ntsc"
        elif fps == 48:
            fps_unit = "show"
        elif fps == 50:
            fps_unit = "palf"
        elif fps == 60:
            fps_unit = "ntscf"
        logger.info('Setting FPS : {}, unit: {}'.format(fps, fps_unit))
        cmds.currentUnit(time=fps_unit)


def save(context_id, session, temp=False):
    '''Save scene locally, with the next version number based on latest version
    in ftrack.'''

    save_path, message = get_save_path(
        context_id, session, extension='.mb', temp=temp
    )

    if save_path is None:
        return (False, message)

    # Save Maya scene to this path
    cmds.file(rename=save_path)
    cmds.file(save=True)
    message = 'Saved Maya scene @ "{}"'.format(save_path)

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
