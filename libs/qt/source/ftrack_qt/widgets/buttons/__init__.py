from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.buttons.circular_button import CircularButton
from ftrack_qt.widgets.buttons.options_button import OptionsButton


class ApproveButton(QtWidgets.QPushButton):
    def __init__(self, label, width=40, height=35, parent=None):
        super(ApproveButton, self).__init__(label, parent=parent)
        self.setMinimumSize(QtCore.QSize(width, height))