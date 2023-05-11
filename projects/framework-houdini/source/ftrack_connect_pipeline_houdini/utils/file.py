# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import hou

from ftrack_connect_pipeline import utils as core_utils


def import_scene(path, context_data=None, options=None):
    '''
    Import the scene from the given *path*, *context_data* and *options*.
    '''

    node = hou.node('/obj').createNode('subnet', context_data['asset_name'])
    node.loadItemsFromFile(path.replace('\\', '/'))
    node.setSelected(True)
    node.moveToGoodPosition()

    return node


def merge_scene(path, context_data=None, options=None):
    '''
    Create LiveGroup from the given *path*, *context_data* and *options*.
    '''
    if options.get('MergeOverwriteOnConflict') is True:
        hou.hipFile.merge(path.replace('\\', '/'), overwrite_on_conflict=True)
    else:
        hou.hipFile.merge(path.replace('\\', '/'))
    return path


def open_scene(path, context_data=None, options=None):
    '''
    Open houdini scene from the given *path*, *context_data* and *options*.
    '''
    hou.hipFile.load(path.replace('\\', '/'))
    return path


def save_scene(context_id, session, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on *context_id* latest version
    in ftrack.'''

    save_path, message = core_utils.get_save_path(
        context_id,
        session,
        extension='.hip{}'.format('nc' if hou.isApprentice() else ''),
        temp=temp,
    )

    if save_path is None:
        return False, message

    # Save Houdini scene to this path
    if save:
        hou.hipFile.save(save_path)
        message = 'Saved Houdini scene @ "{}"'.format(save_path)
    else:
        hou.hipFile.setName(save_path)
        message = 'Renamed Houdini scene @ "{}"'.format(save_path)

    result = save_path

    return result, message
