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
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import Dialog


class QtAssetManagerClient(AssetManagerClient, QtWidgets.QFrame):
    '''
    QtAssetManagerClient class.
    '''

    assets_discovered = QtCore.Signal()

    client_name = 'asset_manager'
    definition_filter = 'asset_manager'  # Use only definitions that matches the definition_filter

    def __init__(
        self,
        event_manager,
        asset_list_model,
        parent_window,
        is_assembler=False,
        parent=None,
    ):
        '''Initialise AssetManagerClient with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        self._asset_list_model = asset_list_model
        self._parent_window = parent_window

        QtWidgets.QFrame.__init__(self, parent=parent)
        AssetManagerClient.__init__(self, event_manager)

        if self.get_theme():
            self.setTheme(self.get_theme())
            if is_assembler:
                # Override AM background color
                self.setProperty('background', 'transparent')
            elif self.get_background_color():
                self.setProperty('background', self.get_background_color())

        self.is_assembler = is_assembler
        self.asset_manager_widget = AssetManagerWidget(self, asset_list_model)
        self.asset_manager_widget.rebuild.connect(self.rebuild)

        self._host_connection = None

        self.pre_build()
        self.build()
        self.post_build()

        if not self.is_assembler:
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

    def get_parent_window(self):
        '''Return the dialog or DCC app window this client is within.'''
        return self._parent_window

    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        self.setLayout(layout)

    def build(self):
        '''Build widgets and parent them.'''
        if not self.is_assembler:
            self.header = header.Header(self.session)
            self.layout().addWidget(self.header)

            self.context_selector = ContextSelector(self, self.session)
            self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

            self.layout().addWidget(line.Line())

            self.host_selector = host_selector.HostSelector()
            self.host_selector.setVisible(False)
            self.layout().addWidget(self.host_selector)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll, 100)

        if self.is_assembler:
            button_widget = QtWidgets.QWidget()
            button_widget.setLayout(QtWidgets.QHBoxLayout())
            button_widget.layout().addStretch()
            self._remove_button = RemoveButton('REMOVE FROM SCENE')
            self._remove_button.setMinimumHeight(32)
            self._remove_button.setEnabled(False)
            button_widget.layout().addWidget(self._remove_button)
            self.layout().addWidget(button_widget)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        if not self.is_assembler:
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

        if self.is_assembler:
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
        # self.asset_manager_widget.set_asset_list(self.asset_entities_list)
        if not host_connection:
            return

        if not AssetManagerClient.change_host(self, host_connection):
            Dialog(
                self.get_parent_window(),
                title='Asset Manager',
                message='No asset manager definitions are available, please check your configuration!',
            )
            return

        self.asset_manager_widget.host_connection = self.host_connection

        self.rebuild()
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

    # Implementation of assetmanager client callbacks

    def _reset_asset_list(self):
        '''Empty the :obj:`asset_entities_list`'''
        self._asset_list_model.reset()

    def rebuild(self):
        '''
        Refreshes the ui running the discover_assets()
        '''
        if not self.host_connection:
            return
        self.discover_assets()

    def _asset_discovered_callback(self, event):
        '''
        Callback function of the discover_assets. Sets the updated
        asset_entities_list.
        '''
        print('@@@ _asset_discovered_callback;')
        if not event['data']:
            self.assets_discovered.emit()
            return
        asset_entities_list = []
        for ftrack_asset in event['data']:
            if ftrack_asset not in self._asset_list_model.items():
                ftrack_asset['session'] = self.session
                asset_entities_list.append(ftrack_asset)

        self.asset_manager_widget.set_asset_list(asset_entities_list)
        self.assets_discovered.emit()

    # Select

    def _on_select_assets(self, asset_info_list):
        '''
        Triggered when select action is clicked on the ui.
        '''
        self.select_assets(asset_info_list)

    def _asset_selection_updated(self, selected_assets):
        self._remove_button.setEnabled(len(selected_assets) > 0)

    def _on_assets_updated(self, event):
        '''Generic asset update'''
        if not event['data']:
            return
        data = event['data']
        do_refresh = None
        for key, value in data.items():
            index = self._asset_list_model.getIndex(key)
            if index is None:
                continue
            self.logger.debug(
                'Updating id {} with index {}'.format(key, index)
            )
            asset_info = value.get(list(value.keys())[0])
            print(
                '@@@ _on_assets_updated; index: {},\n asset_info: {}, \n event: {}'
            ).format(index, asset_info, event)
            self._asset_list_model.setData(index, asset_info, silent=True)
            do_refresh = True
        if do_refresh:
            self.asset_manager_widget.refresh.emit()

    # Load

    def _on_load_assets(self, asset_info_list):
        '''
        Triggered when load action is clicked on the ui.
        '''
        self.load_assets(asset_info_list)

    def _load_assets_callback(self, event):
        '''
        Callback function of the load_assets. Updates the ui.
        '''
        self._on_assets_updated(event)

    # Update

    def _on_update_assets(self, asset_info_list, plugin):
        '''
        Triggered when update action is clicked on the ui.
        '''
        self.update_assets(asset_info_list, plugin)

    def _update_assets_callback(self, event):
        '''
        Callback of the :meth:`update_assets`
        Updates the current asset_entities_list
        '''
        self._on_assets_updated(event)

    # Change version

    def _on_change_asset_version(self, asset_info, new_version_id):
        '''
        Triggered when a version of the asset has changed on the ui.
        '''
        self.change_version(asset_info, new_version_id)

    def _change_version_callback(self, event):
        '''
        Callback function of the change_version. Updates the ui.
        '''
        self._on_assets_updated(event)

    # Unload

    def _on_unload_assets(self, asset_info_list):
        '''
        Triggered when unload action is clicked on the ui.
        '''
        self.unload_assets(asset_info_list)

    def _unload_assets_callback(self, event):
        '''
        Callback function of the unload_assets. Updates the ui.
        '''
        self._on_assets_updated(event)

    # Remove

    def _remove_assets_clicked(self):
        self._on_remove_assets(
            self.asset_manager_widget.asset_list.selection()
        )

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
        if not event['data']:
            return
        data = event['data']

        do_refresh = None
        for key, value in data.items():
            index = self._asset_list_model.getIndex(key)
            if index is None:
                continue
            self.logger.debug(
                'Updating id {} with index {}'.format(key, index)
            )
            self._asset_list_model.removeRows(index, silent=True)
            do_refresh = True
        if do_refresh:
            self.asset_manager_widget.refresh.emit()

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.RightButton:
            self.asset_manager_widget.asset_list.clear_selection()
        return super(QtAssetManagerClient, self).mousePressEvent(event)


class RemoveButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(RemoveButton, self).__init__(label, parent=parent)
        self.setIcon(qta.icon('mdi6.close', color='#E74C3C'))
