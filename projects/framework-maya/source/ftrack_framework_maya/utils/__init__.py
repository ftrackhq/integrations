# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import maya.cmds as cmds
import maya.OpenMayaUI as omui

from shiboken2 import wrapInstance
from Qt import QtWidgets, QtCore


# Dock widget in Maya
def maya_dock_right(widget):
    '''Dock *widget* to the right side of Maya.'''
    print(widget)
    dock_control_name = widget.windowTitle() + '_dock'
    if cmds.workspaceControl(dock_control_name, q=True, exists=True):
        cmds.deleteUI(dock_control_name)
    widget_size = widget.size()
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

    # cmds.workspaceControl(
    #     dock_control_name,
    #     label=widget.windowTitle(),
    #     dockToMainWindow=('right', False),
    #     retain=False,
    #     iw=widget_size.width(),
    #     ih=widget_size.width(),
    #     wp='preferred',
    #     hp='preferred',
    #     r=True,
    #     rs=True,
    #     #alm=True,# TODO: this one might be interesting to active >maya 2023
    #     floating=False,
    #     visible=True
    # )
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
