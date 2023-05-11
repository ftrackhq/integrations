# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import hou, hdefereval

from ftrack_connect_pipeline_houdini.constants import asset as asset_const


def get_current_scene_objects():
    '''Return all objects within the houdini scene'''
    return set(hou.node('/obj').glob('*'))


def get_ftrack_nodes(as_node=False):
    '''Return all ftrack node paths within the scene. If *as_node* is True, the node
    hou.Node object will be returned instead of the path.'''
    result = []
    for node in hou.node('/').allSubChildren():
        if node.parmTemplateGroup().findFolder('ftrack'):
            parameter = node.parm(asset_const.ASSET_INFO_ID)
            if parameter is not None:
                value_ftrack_id = parameter.eval()
                if value_ftrack_id != '':
                    result.append(node.path() if not as_node else node)
    return set(result)


def get_connected_objects(name):
    '''
    Return all the Houdini nodes linked to the ftrack node by *name*.

    :return: List of Houdini Node objects
    '''
    result = []
    for node in hou.node('/').allSubChildren():
        if node.parmTemplateGroup().findFolder('ftrack'):
            parameter = node.parm(asset_const.ASSET_LINK)
            if parameter:
                linked_ftrack_node_name = parameter.eval()
                if linked_ftrack_node_name == name:
                    result.append(node)
    return result
