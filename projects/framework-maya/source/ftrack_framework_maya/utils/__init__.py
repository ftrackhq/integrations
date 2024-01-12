# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import maya.cmds as cmds
import maya.OpenMayaUI as omui

from shiboken2 import wrapInstance
from Qt import QtWidgets


# Dock widget in Maya
def maya_dock_right(widget):
    '''Dock *widget* to the right side of Maya.'''
    print(widget)
    dock_control_name = widget.windowTitle() + '_dock'
    if cmds.workspaceControl(dock_control_name, q=True, exists=True):
        cmds.deleteUI(dock_control_name)

    cmds.workspaceControl(
        dock_control_name,
        label=widget.windowTitle(),
        dockToMainWindow=('right', 1),
    )
    dock_control_ptr = omui.MQtUtil.findControl(dock_control_name)
    dock_control_widget = wrapInstance(
        int(dock_control_ptr), QtWidgets.QWidget
    )
    cmds.workspaceControl(
        dock_control_name, edit=True, addControl=dock_control_ptr
    )

    print(f"dock_control_ptr{dock_control_ptr}")
    print(f"dock_control_widget{dock_control_widget}")
    widget.setParent(dock_control_widget)
    widget.show_ui()
    widget.show()
    widget.raise_()
    widget.activateWindow()
    widget.setFocus()
    print(dir(widget))
