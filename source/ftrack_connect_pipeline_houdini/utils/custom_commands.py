# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import logging

import hou

logger = logging.getLogger(__name__)

def get_current_scene_objects():
    return set(hou.node('/obj').glob('*'))

def get_ftrack_objects():
    result = []
    for obj in hou.node('/').allSubChildren():
        if obj.parmTemplateGroup().findFolder('ftrack'):
            valueftrackId = obj.parm('component_id').eval()
            if valueftrackId != '':
                result.append(obj)
    return set(result)

def import_scene(path, context=None, options=None):
    '''
    Import the scene from the given *path*
    '''

    node = hou.node('/obj').createNode(
        'subnet', context['asset_name'])
    node.loadChildrenFromFile(path.replace('\\', '/'))
    node.setSelected(1)
    node.moveToGoodPosition()

    return node

def merge_scene(path, context=None, options=None):
    '''
    Create LiveGroup from the given *path*
    '''
    if options.get('MergeOverwriteOnConflict') is True:
        hou.hipFile.merge(path.replace('\\', '/'), overwrite_on_conflict=True)
    else:
        hou.hipFile.merge(path.replace('\\', '/'))
    return path

def open_scene(path, context=None, options=None):
    '''
    Open houdini scene from the given *path*
    '''
    hou.hipFile.load(path.replace('\\', '/'))
    return path

