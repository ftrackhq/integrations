#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial

from ftrack_connect_pipeline.client.asset_manager import AssetManagerClient
from Qt import QtWidgets, QtCore, QtCompat, QtGui
from ftrack_connect_pipeline_qt.ui.utility.widget import header, host_selector
from ftrack_connect_pipeline_qt.ui.asset_manager import AssetManagerWidget


class QtAssetManagerClient(AssetManagerClient, QtWidgets.QWidget):
    '''
    QtAssetManagerClient class.
    '''
    definition_filter = 'asset_manager'
    '''Use only definitions that matches the definition_filter'''

    def __init__(self, event_manager, parent=None):
        '''Initialise AssetManagerClient with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        QtWidgets.QWidget.__init__(self, parent=parent)
        AssetManagerClient.__init__(self, event_manager)

        self.asset_manager_widget = AssetManagerWidget(event_manager)
        self.asset_manager_widget.set_asset_list(self.asset_entities_list)

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
        AssetManagerClient._host_discovered(self, event)
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

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.host_changed.connect(self.change_host)
        self.refresh_button.clicked.connect(partial(self._refresh_ui, None))

        self.asset_manager_widget.widget_status_updated.connect(
            self._on_widget_status_updated
        )
        self.asset_manager_widget.change_asset_version.connect(
            self._on_change_asset_version
        )

        self.asset_manager_widget.select_assets.connect(
            self._on_select_assets
        )

        self.asset_manager_widget.remove_assets.connect(
            self._on_remove_assets
        )

        self.asset_manager_widget.update_assets.connect(
            self._on_update_assets
        )

    def _on_widget_status_updated(self, data):
        ''' Triggered when a widget emits the
        widget_status_update signal.
        Sets the status from the given *data* to the header
        '''
        status, message = data
        self.header.setMessage(message, status)

    def _on_change_asset_version(self, asset_info, new_version_id):
        '''
        Triggered when a version of the asset has changed on the ui.
        '''
        self.change_version(asset_info, new_version_id)

    def _change_version_callback(self, event):
        '''
        Callback function of the change_version. Updates the ui.
        '''
        AssetManagerClient._change_version_callback(self, event)
        self.update()

    def _on_select_assets(self, asset_info_list):
        '''
        Triggered when select action is clicked on the ui.
        '''
        self.select_assets(asset_info_list)

    def _on_remove_assets(self, asset_info_list):
        '''
        Triggered when remove action is clicked on the ui.
        '''
        self.remove_assets(asset_info_list)

    def _remove_assets_callback(self, event):
        '''
        Callback function of the remove_asset. Sets the updated
        asset_entities_list.
        '''
        AssetManagerClient._remove_assets_callback(self, event)
        self.asset_manager_widget.set_asset_list(self.asset_entities_list)

    def _on_update_assets(self, asset_info_list, plugin):
        '''
        Triggered when update action is clicked on the ui.
        '''
        self.update_assets(asset_info_list, plugin)

    def _update_assets_callback(self, event):
        '''
        Callback function of the update_assets. Updates the ui.
        '''
        AssetManagerClient._update_assets_callback(self, event)
        self.update()

    def change_host(self, host_connection):
        '''
        Triggered host is selected in the host_selector.
        '''

        self._reset_asset_list()
        self.asset_manager_widget.set_asset_list(self.asset_entities_list)
        if not host_connection:
            return

        AssetManagerClient.change_host(self, host_connection)

        self.asset_manager_widget.set_host_connection(self.host_connection)

        self.discover_assets()
        self.asset_manager_widget.engine_type = self.engine_type
        self.asset_manager_widget.set_context_actions(self.menu_action_plugins)

        self.scroll.setWidget(self.asset_manager_widget)

    def _asset_discovered_callback(self, event):
        '''
        Callback function of the discover_assets. Sets the updated
        asset_entities_list.
        '''
        AssetManagerClient._asset_discovered_callback(self, event)
        self.asset_manager_widget.set_asset_list(self.asset_entities_list)

    def _refresh_ui(self, event):
        '''
        Refreshes the ui running the discover_assets()
        '''
        if not self.host_connection:
            return
        self.discover_assets()