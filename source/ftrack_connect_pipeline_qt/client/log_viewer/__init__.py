#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial
import os
import sys
import subprocess
import sqlite3
import json
import base64

from Qt import QtGui, QtCore, QtWidgets
from ftrack_connect_pipeline import client, constants
from ftrack_connect_pipeline.configure_logging import get_log_directory
from ftrack_connect_pipeline.client.log_viewer import LogViewerClient
from ftrack_connect_pipeline_qt.ui.log_viewer import LogViewerWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import header, host_selector
from ftrack_connect_pipeline.database import get_database_path
from ftrack_connect_pipeline.log.log_item import LogItem

class QtLogViewerClient(LogViewerClient, QtWidgets.QWidget):
    '''
    QtAssetManagerClient class.
    '''
    definition_filter = 'log_viewer'
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
        Adds the given *hosts*
        '''
        for host_connection in host_connections:
            if host_connection in self.host_connections:
                continue
            self._host_connections.append(host_connection)

    def _host_discovered(self, event):
        '''callback, adds new hosts connection from the given *event* to the
        host_selector'''
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

    def update_log_items(self):
        ''' Connect to persistent log storage and fetch records. '''

        con = sqlite3.connect(get_database_path())
        cur = con.cursor()

        log_items = []
        if not self.host_connection is None:
            cur.execute(' SELECT status,widget_ref,host_id,execution_time,'
                'plugin_name,result,message,user_message,plugin_type FROM log WHERE'
                ' host_id=?;  ', (
                    self.host_connection.id, 
            ))

            for t in cur.fetchall():
                log_items.append(LogItem({
                    'status':t[0],
                    'widget_ref':t[1],
                    'host_id':t[2],
                    'execution_time':t[3],
                    'plugin_name':t[4],
                    'result':json.loads(base64.b64decode(t[5]).decode('utf-8')),
                    'message':t[6],
                    'user_message':t[7],
                    'plugin_type':t[8],
                }))

        con.close()

        self.log_viewer_widget.set_log_items(log_items)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.host_changed.connect(self.change_host)
        self.refresh_button.clicked.connect(partial(self._refresh_ui, None))
        self.open_log_folder_button.clicked.connect(
            self._on_logging_button_clicked
        )
        self.log_item_added.connect(self.update_log_items)

    def _add_log_item(self, log_item):
        ''' Override client function, update view. '''
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

    def _refresh_ui(self, event):
        '''
        Refreshes the ui
        '''
        if not self.host_connection:
            return
        self.update_log_items()