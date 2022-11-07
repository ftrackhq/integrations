# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

import ftrack_connect_pipeline.constants as constants

import ftrack_connect_pipeline_qt.constants as qt_constants
from ftrack_connect_pipeline_qt.client.publish import QtPublisherClientWidget

import ftrack_connect_pipeline_3dsmax.constants as max_constants


class MaxQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        max_constants.UI_TYPE,
    ]

    '''Dockable Max publisher widget'''

    def __init__(self, event_manager, parent=None):
        self.dock_widget = QtWidgets.QDockWidget(parent=parent)
        super(MaxQtPublisherClientWidget, self).__init__(
            event_manager, parent=self.dock_widget
        )
        self.setWindowTitle('Max Pipeline Publisher')
        self.setObjectName('Max Pipeline Publisher')
        self.dock_widget.setWidget(self)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.setFloating(False)

    def show(self):
        self.dock_widget.show()
        super(MaxQtPublisherClientWidget, self).show()

    def get_theme_background_style(self):
        return 'max'


class MaxQtPublisherClientWidgetTEST(QtWidgets.QFrame):
    def __init__(self, event_manager, parent=None):
        self.dock_widget = QtWidgets.QDockWidget(parent=parent)
        super(MaxQtPublisherClientWidgetTEST, self).__init__(
            parent=self.dock_widget
        )
        self.setWindowTitle('Max Pipeline Publisher')
        self.setObjectName('Max Pipeline Publisher')
        self.dock_widget.setWidget(self)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.setFloating(True)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel('My mock publisher content'))

    def show(self):
        self.dock_widget.show()
        super(MaxQtPublisherClientWidgetTEST, self).show()
