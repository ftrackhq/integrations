# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.ui.utility.widget import icon


class RunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(RunButton, self).__init__(label, parent=parent)
        self.setMaximumHeight(32)
        self.setMinimumHeight(32)


class RemoveButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(RemoveButton, self).__init__(label, parent=parent)
        self.setIcon(icon.MaterialIcon('close', color='#E74C3C'))


class AddRunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(AddRunButton, self).__init__(label, parent=parent)
        self.setMaximumHeight(32)
        self.setMinimumHeight(32)
        self.setToolTip('Add asset(s) but do not load yet')


class LoadRunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(LoadRunButton, self).__init__(label, parent=parent)
        self.setMaximumHeight(32)
        self.setMinimumHeight(32)
        self.setToolTip('Add asset(s) and load them')


class OpenAssemblerButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(OpenAssemblerButton, self).__init__(
            'OPEN ASSEMBLER', parent=parent
        )
        self.setMinimumWidth(128)
        self.setMaximumHeight(32)
        self.setMinimumHeight(32)


class DenyButton(QtWidgets.QPushButton):
    def __init__(self, label, width=40, height=35, parent=None):
        super(DenyButton, self).__init__(label, parent=parent)
        self.setMinimumSize(QtCore.QSize(width, height))


class ApproveButton(QtWidgets.QPushButton):
    def __init__(self, label, width=40, height=35, parent=None):
        super(ApproveButton, self).__init__(label, parent=parent)
        self.setMinimumSize(QtCore.QSize(width, height))


class NewAssetButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(NewAssetButton, self).__init__('NEW', parent=parent)
        self.setStyleSheet('background: #FFDD86;')


class OptionsButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(OptionsButton, self).__init__(parent=parent)
