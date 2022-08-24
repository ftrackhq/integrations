# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
import logging
import threading
from functools import wraps

import hou, hdefereval

from ftrack_connect_pipeline_houdini.constants import asset as asset_const
from ftrack_connect_pipeline.utils import (
    get_save_path,
)

logger = logging.getLogger(__name__)


def get_current_scene_objects():
    return set(hou.node('/obj').glob('*'))


def get_ftrack_objects(as_node=False):
    result = []
    for node in hou.node('/').allSubChildren():
        if node.parmTemplateGroup().findFolder('ftrack'):
            parameter = node.parm(asset_const.ASSET_INFO_ID)
            if parameter is not None:
                valueftrackId = parameter.eval()
                if valueftrackId != '':
                    result.append(node.path() if not as_node else node)
    return set(result)


def import_scene(path, context_data=None, options=None):
    '''
    Import the scene from the given *path*
    '''

    node = hou.node('/obj').createNode('subnet', context_data['asset_name'])
    node.loadItemsFromFile(path.replace('\\', '/'))
    node.setSelected(True)
    node.moveToGoodPosition()

    return node


def merge_scene(path, context_data=None, options=None):
    '''
    Create LiveGroup from the given *path*
    '''
    if options.get('MergeOverwriteOnConflict') is True:
        hou.hipFile.merge(path.replace('\\', '/'), overwrite_on_conflict=True)
    else:
        hou.hipFile.merge(path.replace('\\', '/'))
    return path


def open_scene(path, context_data=None, options=None):
    '''
    Open houdini scene from the given *path*
    '''
    hou.hipFile.load(path.replace('\\', '/'))
    return path


def init_houdini(context_id=None, session=None):
    '''
    Initialise timeline in Houdini based on shot/asset build settings.

    :param session:
    :param context_id: If provided, the timeline data should be fetched this context instead of environment variables.
    :param session: The session required to query from *context_id*.
    :return:
    '''
    fstart = fend = fps = None
    if context_id:
        assert session is not None, 'Session not provided'
        context = session.query(
            'Context where id={}'.format(context_id)
        ).first()
        if context is None:
            logger.error(
                'Cannot initialize Houdini timeline - no such context: {}'.format(
                    context_id
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
                'Cannot initialize Houdini timeline - no shot related to context: {}'.format(
                    context_id
                )
            )
            return
        elif (
            not 'fstart' in shot['custom_attributes']
            or not 'fend' in shot['custom_attributes']
        ):
            logger.warning(
                'Cannot initialize Houdini timeline - no fstart or fend shot custom attributes available'.format()
            )
            return
        if 'fstart' in shot['custom_attributes']:
            fstart = float(shot['custom_attributes']['fstart'])
        if 'fend' in shot['custom_attributes']:
            fend = float(shot['custom_attributes']['fend'])
        if 'fps' in shot['custom_attributes']:
            fps = float(shot['custom_attributes']['fps'])
    else:
        # Set default values from environments.
        if 'FS' in os.environ and len(os.environ['FS'] or '') > 0:
            fstart = float(os.environ.get('FS', 0))
        if 'FE' in os.environ and len(os.environ['FE'] or '') > 0:
            fend = float(os.environ.get('FE', 100))
        if 'FPS' in os.environ and len(os.environ['FPS'] or '') > 0:
            fps = float(os.environ['FPS'])

    if fstart is not None and fend is not None:
        logger.info('Setting frame range: {}-{}'.format(fstart, fend))
        hou.hscript('tset {0} {1}'.format(fstart / fps, fend / fps))
        hou.playbar.setPlaybackRange(fstart, fend)
        hou.setFrame(fstart)

    if fps is not None:
        logger.info('Setting FPS : {}'.format(fps))
        hou.setFps(fps)


def run_in_main_thread(f):
    '''Make sure a function runs in the main Maya thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            return hdefereval.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated


def save(context_id, session, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on latest version
    in ftrack.'''

    save_path, message = get_save_path(
        context_id,
        session,
        extension='.hip{}'.format('nc' if hou.isApprentice() else ''),
        temp=temp,
    )

    if save_path is None:
        return (False, message)

    # Save Houdini scene to this path
    if save:
        hou.hipFile.save(save_path)
        message = 'Saved Houdini scene @ "{}"'.format(save_path)
    else:
        hou.hipFile.setName(save_path)
        message = 'Renamed Houdini scene @ "{}"'.format(save_path)

    result = save_path

    return result, message
