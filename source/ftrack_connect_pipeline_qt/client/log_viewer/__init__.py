#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial
import os
import sys
import subprocess

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline import client, constants
from ftrack_connect_pipeline.client.log_viewer import LogViewerClient
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.log_viewer.plugin_log import (
    PluginLogViewerWidget,
)
from ftrack_connect_pipeline_qt.ui.log_viewer.file_log import (
    FileLogViewerWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    host_selector,
    header,
    tab,
)
from ftrack_connect_pipeline_qt.ui import resource
from ftrack_connect_pipeline_qt.ui import theme
from ftrack_connect_pipeline_qt.ui.utility.widget import icon
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog


class QtLogViewerDialog(dialog.Dialog):
    def __init__(self, event_manager, parent=None):
        super(QtLogViewerDialog, self).__init__(parent=parent)

        if self.getTheme():
            self.setTheme(self.getTheme())
            if self.getThemeBackgroundStyle():
                self.setProperty('background', self.getThemeBackgroundStyle())
        self.setProperty('docked', 'false')

        self.client = QtLogViewerClient(event_manager, None)

        self.shown = False

        self.pre_build()
        self.build()
        self.post_build()

    def getTheme(self):
        '''Return the client theme, return None to disable themes. Can be overridden by child.'''
        return 'dark'

    def setTheme(self, selected_theme):
        theme.applyFont()
        theme.applyTheme(self, selected_theme, 'plastique')

    def getThemeBackgroundStyle(self):
        return 'ftrack'

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 5)
        self.layout().setSpacing(1)

    def build(self):
        self.layout().addWidget(self.client)

    def post_build(self):
        self.setWindowTitle('ftrack Log viewer')
        self.resize(750, 630)
        self.setModal(True)

    def show(self):
        if self.shown:
            # Widget has been shown before, reset client
            pass
        super(QtLogViewerDialog, self).show()
        self.shown = True


class QtLogViewerClient(LogViewerClient, QtWidgets.QWidget):
    '''
    QtLogViewerClient class.
    '''

    # LOG_MODE_PLUGIN = 0
    # LOG_MODE_FILE = 1

    client_name = qt_constants.LOG_VIEWER_WIDGET
    definition_filter = 'log_viewer'
    '''Use only definitions that matches the definition_filter'''

    logItemAdded = QtCore.Signal(object)

    def __init__(self, event_manager, parent_window, parent=None):
        '''Initialise QtAssetManagerClient with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''
        self._parent_window = parent_window
        # self._log_mode = QtLogViewerClient.LOG_MODE_PLUGIN

        QtWidgets.QWidget.__init__(self, parent=parent)
        LogViewerClient.__init__(self, event_manager)

        self._host_connection = None

        self.pre_build()
        self.build()
        self.post_build()
        self.add_hosts(self.discover_hosts())

    def get_parent_window(self):
        '''Return the dialog or DCC app window this client is within.'''
        return self._parent_window

    def is_docked(self):
        False

    def add_hosts(self, host_connections):
        '''
        Adds the given *host_connections*

        *host_connections* : list of
        :class:`~ftrack_connect_pipeline.client.HostConnection`
        '''
        for host_connection in host_connections:
            if host_connection in self.host_connections:
                continue
            self._host_connections.append(host_connection)

    def _host_discovered(self, event):
        '''
        Callback, add the :class:`~ftrack_connect_pipeline.client.HostConnection`
        of the new discovered :class:`~ftrack_connect_pipeline.host.HOST` from
        the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        LogViewerClient._host_discovered(self, event)
        self.host_selector.add_hosts(self.host_connections)

        self.host_selector.setVisible(len(self.host_connections) > 1)

    def change_host(self, host_connection):
        '''
        Triggered host is selected in the host_selector.
        '''

        if not host_connection:
            return

        LogViewerClient.change_host(self, host_connection)

        self.update_log_items()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(1)

        self._plugin_log_viewer_widget = PluginLogViewerWidget(
            self.get_parent_window(), self.event_manager
        )

        self._file_log_viewer_widget = FileLogViewerWidget(
            self.get_parent_window()
        )

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(
            self.session, parent=self.get_parent_window()
        )
        self.layout().addWidget(self.header)

        self.host_selector = host_selector.HostSelector()
        self.layout().addWidget(self.host_selector)
        self.host_selector.setVisible(False)

        # Add tabbed pane
        self._tab_widget = tab.TabWidget()

        self._tab_widget.addTab(self._plugin_log_viewer_widget, 'Plugin log')

        self._tab_widget.addTab(self._file_log_viewer_widget, 'File log')

        self.layout().addWidget(self._tab_widget)

    def update_log_items(self):
        '''Connect to persistent log storage and fetch records.'''
        self._plugin_log_viewer_widget.set_log_items(self.logs)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.hostChanged.connect(self.change_host)
        self._plugin_log_viewer_widget.refresh_button.clicked.connect(
            self._refresh_ui
        )
        self.logItemAdded.connect(self.update_log_items)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        if index == 1:
            self._file_log_viewer_widget.refresh_ui()

    def _on_log_item_added(self, log_item):
        '''Override client function, update view.'''
        self._refresh_ui()

    def _refresh_ui(self):
        '''
        Refreshes the ui setting the :obj:`logs` items to the
        :obj:`log_viewer_widget`
        '''
        if not self.host_connection:
            return
        self.update_log_items()
