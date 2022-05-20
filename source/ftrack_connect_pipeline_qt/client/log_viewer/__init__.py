#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial
import os
import sys
import subprocess

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline import client, constants as client_constants
from ftrack_connect_pipeline.client.log_viewer import LogViewerClient

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.utils import get_theme, set_theme
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

    ui_types = [client_constants.UI_TYPE, qt_constants.UI_TYPE]
    _shown = (
        False  # Flag telling if widget has been shown before and needs refresh
    )

    # LOG_MODE_PLUGIN = 0
    # LOG_MODE_FILE = 1

    logItemAdded = QtCore.Signal(object)

    def __init__(self, event_manager, parent=None):
        '''Initialise QtAssetManagerClient with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''

        dialog.Dialog.__init__(self, parent=parent)
        LogViewerClient.__init__(self, event_manager)

        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())
        self.setProperty('docked', 'false')

        self._host_connection = None

        self.pre_build()
        self.build()
        self.post_build()

        if not self.host_connections:
            self.discover_hosts()

    def get_theme_background_style(self):
        return 'ftrack'

    def is_docked(self):
        False

    # Build

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

        self.host_selector = host_selector.HostSelector(self)
        self.layout().addWidget(self.host_selector)

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

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override)'''
        self.host_selector.add_hosts(host_connections)

    def on_host_changed(self, host_connection):
        '''Triggered when client has set host connection'''
        self.update_log_items()

    # Use

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

    def conditional_rebuild(self):
        '''Reset a client that has become visible after being hidden.'''
        if self._shown:
            # Refresh when re-opened
            self._refresh_ui()
        self._shown = True
