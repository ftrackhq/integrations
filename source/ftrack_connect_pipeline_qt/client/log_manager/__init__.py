#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial
import os, sys, subprocess

from Qt import QtGui, QtCore, QtWidgets
from ftrack_connect_pipeline import client, constants
from ftrack_connect_pipeline.configure_logging import get_log_directory
from ftrack_connect_pipeline.client.log_manager import LogManagerClient
from ftrack_connect_pipeline_qt.ui.log_manager import LogManagerWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import header, host_selector


class QtLogManagerClient(LogManagerClient, QtWidgets.QWidget):
    '''
    QtAssetManagerClient class.
    '''
    definition_filter = 'log_manager'

    def __init__(self, event_manager, parent=None):
        '''Initialise QtAssetManagerClient with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''
        QtWidgets.QWidget.__init__(self, parent=parent)
        LogManagerClient.__init__(self, event_manager)

        self.log_manager_widget = LogManagerWidget(event_manager)

        self.host_connection = None

        self.pre_build()
        self.build()
        self.post_build()
        self.add_hosts(self.discover_hosts())

    def add_hosts(self, hosts):
        '''
        Adds the given *hosts*
        '''
        for host in hosts:
            if host in self.hosts:
                continue
            self._host_list.append(host)

    def _host_discovered(self, event):
        '''callback, adds new hosts connection from the given *event* to the
        host_selector'''
        LogManagerClient._host_discovered(self, event)
        self.host_selector.add_hosts(self.hosts)

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
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed
        )
        self.layout().addWidget(
            self.refresh_button, alignment=QtCore.Qt.AlignRight
        )

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll)

        self.open_log_folder_button = QtWidgets.QPushButton(
            'Open log directory')

        self.layout().addWidget(self.open_log_folder_button)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.host_changed.connect(self.change_host)
        self.refresh_button.clicked.connect(partial(self._refresh_ui, None))
        self.open_log_folder_button.clicked.connect(
            self._on_logging_button_clicked
        )

    def change_host(self, host_connection):
        '''
        Triggered host is selected in the host_selector.
        '''
        LogManagerClient.change_host(self, host_connection)

        self.log_manager_widget.set_log_items(self.log_list)

        self.scroll.setWidget(self.log_manager_widget)

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

    def _refresh_ui(self, event):
        '''
        Refreshes the ui running the discover_assets()
        '''
        if not self.host_connection:
            return
        self.log_manager_widget.set_log_items(self.log_list)