#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline.constants import asset as asset_const
from ftrack_connect_pipeline.client.asset_manager import AssetManagerClient
from ftrack_connect_pipeline_qt.ui.utility.widget.button import RemoveButton

from ftrack_connect_pipeline_qt.utils import get_theme, set_theme
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    host_selector,
    line,
    scroll_area,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.asset_manager import (
    AssetManagerWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import ModalDialog
from ftrack_connect_pipeline_qt.utils import BaseThread, set_property

class QtAssetManagerClient(AssetManagerClient):
    '''
    QtAssetManagerClient class.
    '''

    ui_types = [core_constants.UI_TYPE, qt_constants.UI_TYPE]

    def __init__(self, event_manager):
        super(QtAssetManagerClient, self).__init__(event_manager)
        self.logger.debug('start qt asset manager')

class QtAssetManagerClientWidget(QtAssetManagerClient, QtWidgets.QFrame):
    '''
    QtAssetManagerClientWidget class.
    '''

    assetsDiscovered = (
        QtCore.Signal()
    )  # Assets has been discovered and loaded

    selectionUpdated = QtCore.Signal(object) # Selection has changed

    def __init__(
        self,
        event_manager,
        asset_list_model,
        is_assembler=False,
        parent=None,
    ):
        '''Initialise QtAssetManagerClientWidget

        :*event_manager*: : instance of :class:`~ftrack_connect_pipeline.event.EventManager`

        :*asset_list_model*: : instance of :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.model.AssetListModel`

        :*is_assembler*: : if True, the asset manager is docked inside the assembler

        :*parent*: : The parent window

        '''
        self._asset_list_model = asset_list_model

        QtWidgets.QFrame.__init__(self, parent=parent)
        QtAssetManagerClient.__init__(self, event_manager)

        self.is_assembler = is_assembler
        self._shown = False
        ''' Flag telling if widget has been shown before and needs refresh '''

        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())
        self.setProperty('docked', 'true' if self.is_docked() else 'false')
        self.setObjectName(
            '{}_{}'.format(
                qt_constants.MAIN_FRAMEWORK_WIDGET, self.__class__.__name__
            )
        )

        self.pre_build()
        self.build()
        self.post_build()

        if not self.is_assembler:
            if not self.host_connections:
                self.discover_hosts()
            elif self.host_connection:
                self.on_context_changed(self.host_connection.context_id)

    def get_theme_background_style(self):
        '''Return the theme background color style. Can be overridden by child.'''
        return 'default' if not self.is_assembler else 'transparent'

    def is_docked(self):
        '''Return True if widget is docked and should have corresponding style'''
        return not self.is_assembler

    # Build

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.asset_manager_widget = AssetManagerWidget(
            self, self._asset_list_model
        )

        if self.is_assembler:
            set_property(self, 'assembler', 'true')

    def build(self):
        '''Build widgets and parent them.'''
        if not self.is_assembler:
            self.header = header.Header(
                self.session,
                show_publisher=True,
                parent=self.parent(),
            )
            self.layout().addWidget(self.header)

            self.layout().addWidget(
                line.Line(style='solid', parent=self.parent())
            )

            self.host_selector = host_selector.HostSelector(self)
            self.layout().addWidget(self.host_selector)

            self.context_selector = ContextSelector(
                self.session, parent=self.parent()
            )
            self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

            self.layout().addWidget(line.Line(parent=self.parent()))

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll, 100)

        if self.is_assembler:
            button_widget = QtWidgets.QWidget()
            button_widget.setLayout(QtWidgets.QHBoxLayout())
            button_widget.layout().addStretch()
            button_widget.layout().setContentsMargins(0, 0, 0, 0)
            self._remove_button = RemoveButton('REMOVE FROM SCENE')
            self._remove_button.setMinimumHeight(32)
            self._remove_button.setEnabled(False)
            button_widget.layout().addWidget(self._remove_button)
            self.layout().addWidget(button_widget)
        else:
            self._remove_button = None

    def post_build(self):
        '''Post Build ui method for events connections.'''
        if not self.is_assembler:
            self.header.publishClicked.connect(self._launch_publisher)
            self.context_selector.changeContextClicked.connect(
                self._launch_context_selector
            )

        self.asset_manager_widget.rebuild.connect(self.rebuild)

        if not self.is_assembler:
            self.host_selector.hostChanged.connect(self.change_host)

        self.asset_manager_widget.widgetStatusUpdated.connect(
            self._on_widget_status_updated
        )
        self.asset_manager_widget.changeAssetVersion.connect(
            self._on_change_asset_version
        )

        self.asset_manager_widget.selectAssets.connect(self._on_select_assets)
        self.asset_manager_widget.removeAssets.connect(self._on_remove_assets)
        self.asset_manager_widget.updateAssets.connect(self._on_update_assets)
        self.asset_manager_widget.loadAssets.connect(self._on_load_assets)
        self.asset_manager_widget.unloadAssets.connect(self._on_unload_assets)

        if self.is_assembler:
            self._remove_button.clicked.connect(self._remove_assets_clicked)
            self.asset_manager_widget.asset_list.selectionUpdated.connect(
                self._asset_selection_updated
            )

        self.selectionUpdated.connect(self._on_asset_selection_updated)
        self.setMinimumWidth(300)

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override) Host(s) have been discovered, add to host selector'''
        self.host_selector.add_hosts(host_connections)

    def on_host_changed(self, host_connection):
        '''Triggered when client has set host connection'''
        self._reset_asset_list()
        # self.asset_manager_widget.set_asset_list(self.asset_entities_list)
        if not host_connection:
            return

        if not super(QtAssetManagerClientWidget, self).on_host_changed(
            host_connection
        ):
            ModalDialog(
                self.parent(),
                title='Asset Manager',
                message='No asset manager definitions are available, please check your configuration!',
            )
            return

        self.rebuild()
        self.asset_manager_widget.engine_type = self.engine_type
        self.asset_manager_widget.set_context_actions(self.menu_action_plugins)

        self.scroll.setWidget(self.asset_manager_widget)

    # Context

    def on_context_changed(self, context_id):
        '''(Override) Context has been evaluated'''
        if not self.is_assembler:
            self.context_selector.context_id = context_id

    # Use

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
        self.asset_manager_widget.set_busy(True)
        BaseThread(
            name='discover_assets_thread',
            target=self.discover_assets,
            target_args=(),
        ).start()

    def _asset_discovered_callback(self, event):
        '''
        Callback function of the discover_assets. Sets the updated
        asset_entities_list. Is run async.
        '''
        self.logger.debug('Discovered assets: {}'.format(event))
        try:
            if not event['data']:
                self.assetsDiscovered.emit()
                return
            asset_entities_list = []
            for ftrack_asset in event['data']:
                if ftrack_asset not in self._asset_list_model.items():
                    asset_entities_list.append(ftrack_asset)

            self.asset_manager_widget.set_asset_list(asset_entities_list)
            self.assetsDiscovered.emit()
        finally:
            self.asset_manager_widget.stopBusyIndicator.emit()

    # Select

    def _on_select_assets(self, asset_info_list):
        '''
        Triggered when select action is clicked on the ui.
        '''
        self.asset_manager_widget.set_busy(True)
        BaseThread(
            name='select_assets_thread',
            target=self.select_assets,
            callback=self._assets_selected,
            target_args=[asset_info_list],
        ).start()

    def _assets_selected(self, *args):
        self.asset_manager_widget.stopBusyIndicator.emit()

    def _asset_selection_updated(self, selected_assets):
        self.selectionUpdated.emit(selected_assets)
        self.asset_manager_widget.stopBusyIndicator.emit()

    def _on_asset_selection_updated(self, selected_assets):
        if self.is_assembler:
            self._remove_button.setEnabled(len(selected_assets) > 0)

    # Load

    def _on_load_assets(self, asset_info_list):
        '''
        Triggered when load action is clicked on the ui.
        '''
        self.asset_manager_widget.set_busy(True)
        BaseThread(
            name='load_assets_thread',
            target=self.load_assets,
            target_args=[asset_info_list],
        ).start()

    def _load_assets_callback(self, event):
        '''
        Callback function of the load_assets. Updates the ui.
        '''
        try:
            if not event['data']:
                return
            data = event['data']
            do_refresh = None
            for key, value in data.items():
                asset_info = self._asset_list_model.getDataById(key)
                if asset_info is None:
                    continue
                self.logger.debug(
                    'Updating id {} with loaded status'.format(key)
                )
                # Set to loaded
                asset_info[asset_const.OBJECTS_LOADED] = True
                do_refresh = True
            if do_refresh:
                self.asset_manager_widget.refresh.emit()
        finally:
            self.asset_manager_widget.stopBusyIndicator.emit()

    def _on_update_assets(self, asset_info_list, plugin):
        '''
        Triggered when update action is clicked on the ui.
        '''
        self.asset_manager_widget.set_busy(True)
        BaseThread(
            name='update_assets_thread',
            target=self.update_assets,
            target_args=[asset_info_list, plugin],
        ).start()

    def _update_assets_callback(self, event):
        '''
        Callback of the :meth:`update_assets`
        Updates the current asset_entities_list
        '''
        try:
            data = event['data']
            do_refresh = None
            for key, value in data.items():
                index = self._asset_list_model.getIndex(key)
                if index is None:
                    continue
                self.logger.debug(
                    'Updating id {} @ position {}'.format(key, index)
                )
                asset_info = value.get(list(value.keys())[0])
                self._asset_list_model.setData(index, asset_info, silent=True)
                do_refresh = True
            if do_refresh:
                self.asset_manager_widget.refresh.emit()
        finally:
            self.asset_manager_widget.stopBusyIndicator.emit()

    # Change version

    def _on_change_asset_version(self, asset_info, new_version_id):
        '''
        Triggered when a version of the asset has changed on the ui.
        '''
        self.asset_manager_widget.set_busy(True)
        BaseThread(
            name='change_asset_version_thread',
            target=self.change_version,
            target_args=[asset_info, new_version_id],
        ).start()

    def _change_version_callback(self, event):
        '''
        Callback function of the change_version. Updates the ui.
        '''
        try:
            if not event['data']:
                return
            data = event['data']
            do_refresh = None
            for key, value in data.items():
                index = self._asset_list_model.getIndex(key)
                if index is None:
                    continue
                self.logger.debug(
                    'Updating id {} @ position {}'.format(key, index)
                )
                asset_info = value
                self._asset_list_model.setData(index, asset_info, silent=True)
                do_refresh = True
            if do_refresh:
                self.asset_manager_widget.refresh.emit()
        finally:
            self.asset_manager_widget.stopBusyIndicator.emit()

    # Unload

    def _on_unload_assets(self, asset_info_list):
        '''
        Triggered when unload action is clicked on the ui.
        '''
        self.asset_manager_widget.set_busy(True)
        BaseThread(
            name='unload_assets_thread',
            target=self.unload_assets,
            target_args=[asset_info_list],
        ).start()

    def _unload_assets_callback(self, event):
        '''
        Callback function of the load_assets. Updates the ui.
        '''
        try:
            if not event['data']:
                return
            data = event['data']
            for key, value in data.items():
                asset_info = self._asset_list_model.getDataById(key)
                if asset_info is None:
                    self.logger.warning(
                        'Could not find recently unloaded asset: {} (event: {})'.format(
                            key, event
                        )
                    )
                    continue
                self.logger.debug(
                    'Updating id {} with loaded status'.format(key)
                )
                # Set to loaded
                asset_info[asset_const.OBJECTS_LOADED] = False
                do_refresh = True
            if do_refresh:
                self.asset_manager_widget.refresh.emit()
        finally:
            self.asset_manager_widget.stopBusyIndicator.emit()

    # Remove

    def _remove_assets_clicked(self):
        selection = self.asset_manager_widget.asset_list.selection()
        if self.asset_manager_widget.check_selection(selection):
            if ModalDialog(
                self.parent(),
                title='ftrack Asset manager',
                question='Really remove {} asset{}?'.format(
                    len(selection), 's' if len(selection) > 1 else ''
                ),
                prompt=True,
            ).exec_():
                self._on_remove_assets(selection)

    def _on_remove_assets(self, asset_info_list):
        '''
        Triggered when remove action is clicked on the ui.
        '''
        self.asset_manager_widget.set_busy(True)
        BaseThread(
            name='remove_assets_thread',
            target=self.remove_assets,
            target_args=[asset_info_list],
        ).start()

    def _remove_assets_callback(self, event):
        '''
        Callback function of the remove_asset. Sets the updated
        asset_entities_list.
        '''
        try:
            if not event['data']:
                return
            data = event['data']

            for key, value in data.items():
                index = self._asset_list_model.getIndex(key)
                if index is None:
                    continue
                self.logger.debug(
                    'Removing id {} with index {}'.format(key, index)
                )
                self._asset_list_model.removeRows(index)
        finally:
            self.asset_manager_widget.stopBusyIndicator.emit()

    def conditional_rebuild(self):
        '''(Override)'''
        if self._shown:
            # Refresh when re-opened
            self.asset_manager_widget.rebuild.emit()
        self._shown = True

    def _clear_widget(self):
        if self.scroll and self.scroll.widget():
            self.scroll.widget().deleteLater()

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.RightButton:
            self.asset_manager_widget.asset_list.clear_selection()
        return super(QtAssetManagerClientWidget, self).mousePressEvent(event)

    def _launch_assembler(self):
        '''Open the assembler and close client if dialog'''
        if not self.is_docked():
            self.hide()
        self.host_connection.launch_widget(core_constants.ASSEMBLER)

    def _launch_publisher(self):
        if not self.is_docked():
            self.hide()
        self.host_connection.launch_widget(core_constants.PUBLISHER)

    def _launch_context_selector(self):
        '''Open entity browser.'''
        self.host_connection.launch_widget(core_constants.CHANGE_CONTEXT)
