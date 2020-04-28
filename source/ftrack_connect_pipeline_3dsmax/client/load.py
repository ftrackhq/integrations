# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_qt.client.load import QtLoaderClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_3dsmax.constants as max_constants


class MaxLoaderClient(QtLoaderClient):
    ui = [constants.UI, qt_constants.UI, max_constants.UI]

    '''Dockable maya load widget'''
    def __init__(self, event_manager, parent=None):
        super(MaxLoaderClient, self).__init__(
            event_manager=event_manager, parent=parent
        )
        self.dock_widget = QtWidgets.QDockWidget(parent=parent)
        self.setWindowTitle('Max Pipeline Loader')
        self.setObjectName('Max Pipeline Publisher')
        self.dock_widget.setWidget(self)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
        self.dock_widget.setFloating(True)
        self.dock_widget.show()

    def show(self):
        super(MaxLoaderClient, self).show()
