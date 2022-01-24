#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial
import os
import sys
import subprocess

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline import client, constants
from ftrack_connect_pipeline.configure_logging import get_log_directory
from ftrack_connect_pipeline.client.log_viewer import LogViewerClient
from ftrack_connect_pipeline_qt.ui.log_viewer import LogViewerWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import header, host_selector


class QtLogViewerClient(LogViewerClient, QtWidgets.QWidget):
    '''
    QtLogViewerClient class.
    '''

    definition_filter = 'log_viewer'
    '''Use only definitions that matches the definition_filter'''

    log_item_added = QtCore.Signal(object)

    def __init__(self, event_manager, parent=None):
        '''Initialise QtAssetManagerClient with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''
        QtWidgets.QWidget.__init__(self, parent=parent)
        LogViewerClient.__init__(self, event_manager)

        self.log_viewer_widget = LogViewerWidget(event_manager)

        self._host_connection = None

        self.pre_build()
        self.build()
        self.post_build()
        self.add_hosts(self.discover_hosts())

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

    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)

        self.host_selector = host_selector.HostSelector()
        self.layout().addWidget(self.host_selector)

        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        self.layout().addWidget(
            self.refresh_button, alignment=QtCore.Qt.AlignRight
        )

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll)

        self.open_log_folder_button = QtWidgets.QPushButton(
            'Open log directory'
        )

        self.layout().addWidget(self.open_log_folder_button)

    def update_log_items(self):
        '''Connect to persistent log storage and fetch records.'''
        self.log_viewer_widget.set_log_items(self.logs)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.host_changed.connect(self.change_host)
        self.refresh_button.clicked.connect(self._refresh_ui)
        self.open_log_folder_button.clicked.connect(
            self._on_logging_button_clicked
        )
        self.log_item_added.connect(self.update_log_items)

    def _add_log_item(self, log_item):
        '''Override client function, update view.'''
        self.log_item_added.emit(log_item)

    def change_host(self, host_connection):
        '''
        Triggered host is selected in the host_selector.
        '''

        if not host_connection:
            return

        LogViewerClient.change_host(self, host_connection)

        self.update_log_items()

        self.scroll.setWidget(self.log_viewer_widget)

    def _on_logging_button_clicked(self):
        '''Handle logging button clicked.'''
        directory = get_log_directory()
        self.open_directory(directory)

    def open_directory(self, path):
        '''Open a filesystem directory from *path* in the OS file browser.

        If *path* is a file, the parent directory will be opened. Depending on OS
        support the file will be pre-selected.

        .. note::

            This function does not support file sequence expressions. The path must
            be either an existing file or directory that is valid on the current
            platform.

        '''
        if os.path.isfile(path):
            directory = os.path.dirname(path)
        else:
            directory = path

        if sys.platform == 'win32':
            subprocess.Popen(['start', directory], shell=True)

        elif sys.platform == 'darwin':
            if os.path.isfile(path):
                # File exists and can be opened with a selection.
                subprocess.Popen(['open', '-R', path])

            else:
                subprocess.Popen(['open', directory])

        else:
            subprocess.Popen(['xdg-open', directory])

    def _refresh_ui(self):
        '''
        Refreshes the ui seting the :obj:`logs` items to the
        :obj:`log_viewer_widget`
        '''
        if not self.host_connection:
            return
        self.update_log_items()
