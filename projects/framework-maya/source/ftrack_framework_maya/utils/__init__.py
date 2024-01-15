# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import maya.cmds as cmds
import maya.OpenMayaUI as omui

from shiboken2 import wrapInstance
from Qt import QtWidgets, QtCore


# Dock widget in Maya
def dock_maya_right(widget):
    '''Dock *widget* to the right side of Maya.'''

    dock_control_name = widget.windowTitle() + '_dock'
    if cmds.workspaceControl(dock_control_name, q=True, exists=True):
        cmds.deleteUI(dock_control_name)

    main_control = cmds.workspaceControl(
        dock_control_name,
        ttc=["AttributeEditor", -1],
        iw=300,
        mw=False,
        wp='preferred',
        hp='preferred',
        retain=False,
        label=widget.windowTitle(),
    )

    dock_control_ptr = omui.MQtUtil.findControl(dock_control_name)
    dock_control_widget = wrapInstance(
        int(dock_control_ptr), QtWidgets.QWidget
    )
    dock_control_widget.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    dock_control_widget.layout().addWidget(widget)

    widget.show()
    widget.setFocus()

    cmds.evalDeferred(
        lambda *args: cmds.workspaceControl(main_control, e=True, rs=True)
    )