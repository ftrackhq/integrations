# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCompat

import maya.OpenMayaUI as OpenMayaUI

from ftrack_connect_pipeline_qt.client.open import QtOpenClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_maya.constants as maya_constants

def get_maya_window():
    """Return the QMainWindow for the main Maya window."""

    winptr = OpenMayaUI.MQtUtil.mainWindow()
    if winptr is None:
        raise RuntimeError('No Maya window found.')
    window = QtCompat.wrapInstance(int(winptr))
    assert isinstance(window, QtWidgets.QMainWindow)
    return window

class MayaOpenClient(QtOpenClient):
    '''Open client within dialog'''
    ui_types = [constants.UI_TYPE, qt_constants.UI_TYPE, maya_constants.UI_TYPE]
    definition_extensions_filter = ['.mb', '.ma']

    def __init__(self, event_manager):
        super(MayaOpenClient, self).__init__(event_manager=event_manager)

class MayaOpenDialog(QtWidgets.QDialog):
    '''Maya open dialog'''
    def __init__(self, event_manager, parent=None):
        super(MayaOpenDialog, self).__init__(
            parent=get_maya_window()
        )

        self._client = MayaOpenClient(event_manager)

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self._client)

        self.setModal(True)

        self.setWindowTitle('Open')
        self.resize(450, 530)
