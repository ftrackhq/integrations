# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

import ftrack_framework_core.constants as constants

import ftrack_framework_qt.constants as qt_constants
from ftrack_framework_qt.client.publish import QtPublisherClientWidget

import ftrack_framework_3dsmax.constants as max_constants


class MaxQtPublisherClientWidget(QtPublisherClientWidget):
    ui_types = [
        constants.UI_TYPE,
        qt_constants.UI_TYPE,
        max_constants.UI_TYPE,
    ]

    '''Dockable Max publisher widget'''

    def __init__(self, event_manager, parent=None):
        self.dock_widget = QtWidgets.QDockWidget(parent=parent)
        self.dock_widget.setWindowTitle('ftrack Pipeline Publisher')
        self.dock_widget.setObjectName('ftrack Pipeline Publisher')
        super(MaxQtPublisherClientWidget, self).__init__(
            event_manager, parent=self.dock_widget
        )
        self.dock_widget.setWidget(self)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.setFloating(False)

    def show(self):
        self.dock_widget.show()
        super(MaxQtPublisherClientWidget, self).show()

    def get_theme_background_style(self):
        return 'max'
