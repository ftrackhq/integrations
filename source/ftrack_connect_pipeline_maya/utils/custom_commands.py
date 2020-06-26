# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd
from ftrack_connect_pipeline_maya.constants import asset as asset_const


def get_current_scene_objects():
    return set(cmd.ls(l=True))


def get_ftrack_nodes():
    return cmd.ls(type=asset_const.FTRACK_PLUGIN_TYPE)


def open_file(path, options):
    return cmd.file(path, o=True, f=True)


def import_file(path, options):
    return cmd.file(path, i=True, **options)


def reference_file(path, options):
    return cmd.file(path, r=True, **options)

def remove_reference_node(referenceNode):
    return cmd.file(rfn=referenceNode, rr=True)

def getReferenceNode(assetLink):
    '''Return the references nodes for the given *assetLink*'''
    res = ''
    try:
        res = cmd.referenceQuery(assetLink, referenceNode=True)
    except:
        children = cmd.listRelatives(assetLink, children=True)

        if children:
            for child in children:
                try:
                    res = cmd.referenceQuery(child, referenceNode=True)
                    break

                except:
                    pass
        else:
            return None
    if res == '':
        print 'Could not find reference node'
        return None
    else:
        return res
