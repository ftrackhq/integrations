# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_qt.client.publish import QtPublisherClient
import ftrack_connect_pipeline.constants as constants
import ftrack_connect_pipeline_qt.constants as qt_constants
import ftrack_connect_pipeline_3dsmax.constants as max_constants


class MaxPublisherClient(QtWidgets.QDockWidget, QtPublisherClient):
    ui = [constants.UI, qt_constants.UI, max_constants.UI]

    '''Dockable maya load widget'''
    def __init__(self, event_manager, parent=None):
        super(MaxPublisherClient, self).__init__(
            event_manager=event_manager, parent=parent
        )
        self.setWindowTitle('Max Pipeline Publisher')
        self.setObjectName('Max Pipeline Publisher')
        self.setWidget(self.my_widget)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
        self.setFloating(True)

    def show(self):
        super(MaxPublisherClient, self).show()
