# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import ftrack_connect.ui.application
import ftrack_connect.ui.widget.overlay

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore


class FrameworkConnectWidget(ftrack_connect.ui.application.ConnectWidget):
    name = 'Framework Connect'

    entityChanged = QtCore.Signal(object)

    def __init__(self, session, widget_instance, parent=None):
        '''Instantiate the publisher widget.'''
        super(FrameworkConnectWidget, self).__init__(session, parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # self.publishView = widget(self.session)
        self.widget_instance = widget_instance
        layout.addWidget(self.widget_instance)

        # self.publishView.publishStarted.connect(self._onPublishStarted)

        # self.publishView.publishFinished.connect(self._onPublishFinished)

        # self.entityChanged.connect(self._onEntityChanged)

    # def _onEntityChanged(self):
    #     '''Callback for entityChanged signal.'''
    #     self.blockingOverlay.hide()
    #     self.busyOverlay.hide()
    #
    # def clear(self):
    #     '''Reset the publisher to it's initial state.'''
    #     self._entity = None
    #     self.publishView.clear()

    def getName(self):
        '''Return name of widget.'''
        return self.widget_instance.windowTitle()

    # def setEntity(self, entity):
    #     '''Set the *entity* for the publisher.'''
    #     self._entity = entity
    #     self.entityChanged.emit(entity)
    #
    #     self.publishView.setEntity(entity)
