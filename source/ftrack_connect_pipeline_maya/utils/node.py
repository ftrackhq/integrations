# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import maya.cmds as cmds

from ftrack_connect_pipeline_maya.constants import asset as asset_const


def get_current_scene_objects():
    return set(cmds.ls(l=True))


def get_ftrack_nodes():
    return cmds.ls(type=asset_const.FTRACK_PLUGIN_TYPE)


def remove_reference_node(referenceNode):
    return cmds.file(rfn=referenceNode, rr=True)


def unload_reference_node(referenceNode):
    return cmds.file(unloadReference=referenceNode)


def load_reference_node(referenceNode):
    return cmds.file(loadReference=referenceNode)


def obj_exists(object_name):
    return cmds.objExists(object_name)


def delete_object(object_name):
    return cmds.delete(object_name)


def get_reference_node(assetLink):
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
