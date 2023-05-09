# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import maya.cmds as cmds

from ftrack_connect_pipeline_maya.constants import asset as asset_const


def get_current_scene_objects():
    '''Return all in the current scene'''
    return set(cmds.ls(l=True))


def get_ftrack_nodes():
    '''Return all ftrack nodes in the current scene'''
    return cmds.ls(type=asset_const.FTRACK_PLUGIN_TYPE)


def remove_reference_node(reference_node):
    '''Remove the given Maya reference node *reference_node*'''
    return cmds.file(rfn=reference_node, rr=True)


def unload_reference_node(reference_node):
    '''Unload the given Maya reference node *reference_node*'''
    return cmds.file(unloadReference=reference_node)


def load_reference_node(reference_node):
    '''Load the given Maya reference node *reference_node*'''
    return cmds.file(loadReference=reference_node)


def obj_exists(object_name):
    '''Check if the given Maya node name *object_name* exists'''
    return cmds.objExists(object_name)


def delete_object(object_name):
    '''Delete the given Maya node name *object_name*'''
    return cmds.delete(object_name)


def get_reference_node(asset_link):
    '''Return the references dcc_objects for the given *asset_link*'''
    res = ''
    try:
        res = cmds.referenceQuery(asset_link, referenceNode=True)
    except:
        children = cmds.listRelatives(asset_link, children=True)

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
