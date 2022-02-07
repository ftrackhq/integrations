#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from functools import partial

from Qt import QtWidgets, QtCore, QtCompat, QtGui

import qtawesome as qta

from ftrack_connect_pipeline.client.asset_manager import AssetManagerClient
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    host_selector,
    line,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.asset_manager import (
    AssetManagerWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui import theme


class QtAssetManagerClient(AssetManagerClient, QtWidgets.QFrame):
    '''
    QtAssetManagerClient class.
    '''

    assets_discovered = QtCore.Signal()

    client_name = 'asset_manager'
    definition_filter = 'asset_manager'  # Use only definitions that matches the definition_filter

    def __init__(self, event_manager, parent=None, assembler=False):
        '''Initialise AssetManagerClient with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        QtWidgets.QFrame.__init__(self, parent=parent)
        AssetManagerClient.__init__(self, event_manager)

        if self.get_theme():
            self.setTheme(self.get_theme())
            if assembler:
                # Override AM background color
                self.setProperty('background', 'transparent')
            elif self.get_background_color():
                self.setProperty('background', self.get_background_color())

        self.asset_manager_widget = AssetManagerWidget(
            assembler, event_manager
        )
        self.asset_manager_widget.set_asset_list(self.asset_entities_list)
        self.asset_manager_widget.refresh.connect(self.refresh_ui)

        self._assembler = assembler
        self._host_connection = None

        self.pre_build()
        self.build()
        self.post_build()

        if not self._assembler:
            self.add_hosts(self.discover_hosts())

    def setTheme(self, selected_theme):
        theme.applyFont()
        theme.applyTheme(self, selected_theme, 'plastique')

    def get_theme(self):
        '''Return the client theme, return None to disable themes. Can be overridden by child.'''
        return 'dark'

    def get_background_color(self):
        '''Return the theme background color style. Can be overridden by child.'''
        return 'default'

    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        self.setLayout(layout)

    def build(self):
        '''Build widgets and parent them.'''
        if not self._assembler:
            self.header = header.Header(self.session)
            self.layout().addWidget(self.header)

            self.context_selector = ContextSelector(self.session)
            self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

            self.layout().addWidget(line.Line())

            self.host_selector = host_selector.HostSelector()
            self.host_selector.setVisible(False)
            self.layout().addWidget(self.host_selector)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll, 100)

        if self._assembler:
            button_widget = QtWidgets.QWidget()
            button_widget.setLayout(QtWidgets.QHBoxLayout())
            button_widget.layout().addStretch()
            self._remove_button = RemoveButton('REMOVE FROM SCENE')
            self._remove_button.setEnabled(False)
            button_widget.layout().addWidget(self._remove_button)
            self.layout().layout().addWidget(button_widget)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        if not self._assembler:
            self.host_selector.host_changed.connect(self.change_host)

        self.asset_manager_widget.widget_status_updated.connect(
            self._on_widget_status_updated
        )
        self.asset_manager_widget.change_asset_version.connect(
            self._on_change_asset_version
        )

        self.asset_manager_widget.select_assets.connect(self._on_select_assets)
        self.asset_manager_widget.remove_assets.connect(self._on_remove_assets)
        self.asset_manager_widget.update_assets.connect(self._on_update_assets)
        self.asset_manager_widget.load_assets.connect(self._on_load_assets)
        self.asset_manager_widget.unload_assets.connect(self._on_unload_assets)

        if self._assembler:
            self._remove_button.clicked.connect(self._remove_assets_clicked)
            self.asset_manager_widget.asset_list.selection_updated.connect(
                self._asset_selection_updated
            )

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
        self.host_selector.setVisible(1 < len(self._host_connections))

    def _host_discovered(self, event):
        '''
        Callback, add the :class:`~ftrack_connect_pipeline.client.HostConnection`
        of the new discovered :class:`~ftrack_connect_pipeline.host.HOST` from
        the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        AssetManagerClient._host_discovered(self, event)
        self.host_selector.add_hosts(self.host_connections)

    def change_host(self, host_connection):
        '''
        Triggered host is selected in the host_selector.
        '''

        self._reset_asset_list()
        self.asset_manager_widget.set_asset_list(self.asset_entities_list)
        if not host_connection:
            return

        if not AssetManagerClient.change_host(self, host_connection):
            QtWidgets.QMessageBox.warning(
                self,
                'Asset Manager',
                'No asset manager definitions are available, please check your configuration!',
                QtWidgets.QMessageBox.Ok,
            )
            return

        self.asset_manager_widget.host_connection = self.host_connection

        self.discover_assets()
        self.asset_manager_widget.engine_type = self.engine_type
        self.asset_manager_widget.set_context_actions(self.menu_action_plugins)

        self.scroll.setWidget(self.asset_manager_widget)

    def _on_widget_status_updated(self, data):
        '''Triggered when a widget emits the
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

    def _on_load_assets(self, asset_info_list):
        '''
        Triggered when load action is clicked on the ui.
        '''
        self.load_assets(asset_info_list)

    def _load_assets_callback(self, event):
        '''
        Callback function of the load_assets. Updates the ui.
        '''
        # TODO: update this function to change the collor of the row for example
        # or set up as loaded or something like that
        AssetManagerClient._load_assets_callback(self, event)
        # self.asset_manager_widget.set_asset_list(self.asset_entities_list)

    def _on_unload_assets(self, asset_info_list):
        '''
        Triggered when unload action is clicked on the ui.
        '''
        self.unload_assets(asset_info_list)

    def _unload_assets_callback(self, event):
        '''
        Callback function of the unload_assets. Updates the ui.
        '''
        # TODO: update this function to change the collor of the row for example
        # or set up as loaded or something like that
        AssetManagerClient._unload_assets_callback(self, event)
        # self.asset_manager_widget.set_asset_list(self.asset_entities_list)

    def _asset_discovered_callback(self, event):
        '''
        Callback function of the discover_assets. Sets the updated
        asset_entities_list.
        '''
        AssetManagerClient._asset_discovered_callback(self, event)
        self.asset_manager_widget.set_asset_list(self.asset_entities_list)
        self.assets_discovered.emit()

    def refresh_ui(self):
        '''
        Refreshes the ui running the discover_assets()
        '''
        if not self.host_connection:
            return
        self.discover_assets()

    def _asset_selection_updated(self, selected_assets):
        self._remove_button.setEnabled(len(selected_assets) > 0)

    def _remove_assets_clicked(self):
        self._on_remove_assets(
            self.asset_manager_widget.asset_list.selection()
        )

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.RightButton:
            self.asset_manager_widget.asset_list.clear_selection()
        return super(QtAssetManagerClient, self).mousePressEvent(event)


class RemoveButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(RemoveButton, self).__init__(label, parent=parent)
        self.setIcon(qta.icon('mdi6.close', color='#E74C3C'))
