# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging

import hou

from ftrack_connect_pipeline_houdini.constants import asset as asset_const

logger = logging.getLogger(__name__)


def get_current_scene_objects():
    return set(hou.node('/obj').glob('*'))


def get_ftrack_objects(as_node=False):
    result = []
    for node in hou.node('/').allSubChildren():
        if node.parmTemplateGroup().findFolder('ftrack'):
            valueftrackId = node.parm(asset_const.ASSET_INFO_ID).eval()
            if valueftrackId != '':
                result.append(node.path() if not as_node else node)
    return set(result)


def import_scene(path, context_data=None, options=None):
    '''
    Import the scene from the given *path*
    '''

    node = hou.node('/obj').createNode('subnet', context_data['asset_name'])
    node.loadChildrenFromFile(path.replace('\\', '/'))
    node.set_selected(1)
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
