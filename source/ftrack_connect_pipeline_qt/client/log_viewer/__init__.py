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

# DO NOT REMOVE UNUSED IMPORT - important to keep this in order to have resources
# initialised properly for applying style and providing images & fonts.
from ftrack_connect_pipeline_qt.ui import (
    resource,
)
from ftrack_connect_pipeline_qt.ui import theme
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog


class QtLogViewerClient(LogViewerClient, dialog.Dialog):
    '''
    QtLogViewerClient class.
    '''

    # LOG_MODE_PLUGIN = 0
    # LOG_MODE_FILE = 1

    client_name = qt_constants.LOG_VIEWER_WIDGET
    definition_filter = 'log_viewer'
    '''Use only definitions that matches the definition_filter'''

    logItemAdded = QtCore.Signal(object)

    def __init__(self, event_manager, parent=None):
        '''Initialise QtAssetManagerClient with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''

        dialog.Dialog.__init__(self, parent=parent)
        LogViewerClient.__init__(self, event_manager)

        if self.getTheme():
            self.setTheme(self.getTheme())
            if self.getThemeBackgroundStyle():
                self.setProperty('background', self.getThemeBackgroundStyle())
        self.setProperty('docked', 'false')

        self._host_connection = None

        self.pre_build()
        self.build()
        self.post_build()

        self.add_hosts(self.discover_hosts())

    def getTheme(self):
        '''Return the client theme, return None to disable themes. Can be overridden by child.'''
        return 'dark'

    def setTheme(self, selected_theme):
        theme.applyFont()
        theme.applyTheme(self, selected_theme, 'plastique')

    def getThemeBackgroundStyle(self):
        return 'ftrack'

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
        self.layout().setContentsMargins(16, 16, 16, 16)
        self.layout().setSpacing(0)

        self._plugin_log_viewer_widget = PluginLogViewerWidget(
            self.event_manager, parent=self.parent()
        )

        self._file_log_viewer_widget = FileLogViewerWidget(
            parent=self.parent()
        )

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(self.session, parent=self.parent())
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

        self.setWindowTitle('ftrack Log viewer')
        self.resize(750, 630)
        self.setModal(True)

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
