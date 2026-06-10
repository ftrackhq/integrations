# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
from functools import wraps

import maya.cmds as cmds
import maya.utils as maya_utils
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance

from ftrack_framework_maya.asset import constants as asset_const


# Dock widget in Maya
def dock_maya_right(widget):
    '''Dock *widget* to the right side of Maya.'''
    widget.show()
    # TODO: To provide docking functionality, comment line above and uncomment code below
    # dock_control_name = widget.windowTitle() + '_dock'
    # if cmds.workspaceControl(dock_control_name, q=True, exists=True):
    #     cmds.deleteUI(dock_control_name)
    #
    # main_control = cmds.workspaceControl(
    #     dock_control_name,
    #     ttc=["AttributeEditor", -1],
    #     iw=300,
    #     mw=False,
    #     wp='preferred',
    #     hp='preferred',
    #     retain=False,
    #     label=widget.windowTitle(),
    # )
    #
    # dock_control_ptr = omui.MQtUtil.findControl(dock_control_name)
    # dock_control_widget = wrapInstance(
    #     int(dock_control_ptr), QtWidgets.QWidget
    # )
    # dock_control_widget.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    #
    # dock_control_widget.layout().addWidget(widget)
    #
    # widget.show()
    # widget.setFocus()
    #
    # cmds.evalDeferred(
    #     lambda *args: cmds.workspaceControl(main_control, e=True, rs=True)
    # )


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


def run_in_main_thread(f):
    '''Make sure a function runs in the main Maya thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            return maya_utils.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated
