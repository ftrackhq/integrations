# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect.qt import QtWidgets
from ftrack_connect.qt import QtCore
from ftrack_connect.qt import QtGui

class AdvancedOptionGroup(QtWidgets.QGroupBox):

    def collapse(self, status):
        self.content.setVisible(status)

    def __init__(self, parent=None):
        super(AdvanceOptionGroup, self).__init__(parent=parent)
        self.setTitle('Advanced options')
        self.setCheckable(True)
        self.setFlat(True)
        self.setChecked(False)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.content = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QFormLayout()
        self.content.setLayout(self.content_layout)
        main_layout.addWidget(self.content)
        self.clicked.connect(self.collapse)
        self.clicked.emit()
    def addRow(self, name, widget):
        self.content_layout.addRow(name, widget)