# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtWidgets, QtCompat

import maya.OpenMayaUI as OpenMayaUI

import maya.cmds as cmds

from ftrack_connect_pipeline_maya.constants import asset as asset_const


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
    '''Return the references ftrack_objects for the given *assetLink*'''
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
        print('Could not find reference ftrack_object')
        return None
    else:
        return res


def get_maya_window():
    """Return the QMainWindow for the main Maya window."""

    winptr = OpenMayaUI.MQtUtil.mainWindow()
    if winptr is None:
        raise RuntimeError('No Maya window found.')
    window = QtCompat.wrapInstance(int(winptr))
    assert isinstance(window, QtWidgets.QMainWindow)
    return window
