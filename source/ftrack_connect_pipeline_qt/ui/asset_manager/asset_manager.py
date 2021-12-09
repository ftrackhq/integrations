# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from functools import partial

from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetManagerBaseWidget
)
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import CircularButton

class AssetManagerWidget(AssetManagerBaseWidget):
    '''Base widget of the asset manager and assembler'''
    refresh = QtCore.Signal()
    widget_status_updated = QtCore.Signal(object)
    change_asset_version = QtCore.Signal(object, object)
    select_assets = QtCore.Signal(object)
    remove_assets = QtCore.Signal(object)
    update_assets = QtCore.Signal(object, object)
    load_assets = QtCore.Signal(object)
    unload_assets = QtCore.Signal(object)

    def __init__(self, event_manager, parent=None):
        super(AssetManagerWidget, self).__init__(event_manager, parent=parent)

    def init_header_content(self, layout):
        '''Create toolbar'''
        title = QtWidgets.QLabel('Tracked assets')
        title.setStyleSheet('font-size: 14px;')
        layout.addWidget(title)
        layout.addWidget(self.init_search())
        self._refresh_button = CircularButton('sync', '#87E1EB')
        self._refresh_button.clicked.connect(self._on_refresh)
        layout.addWidget(self._refresh_button)
        self._config_button = CircularButton('cog', '#87E1EB')
        self._config_button.clicked.connect(self._on_config)
        layout.addWidget(self._config_button)

    def _on_refresh(self):
        self.refresh.emit()

    def _on_config(self):
        pass

    def on_asset_change_version(self, index, value):
        '''
        Triggered when a version of the asset has changed on the
        :obj:`version_cb_delegate`
        '''
        _asset_info = self.asset_table_view.asset_model.asset_entities_list[
            index.row()
        ]
        # Copy to avoid update automatically
        asset_info = _asset_info.copy()
        self.change_asset_version.emit(asset_info, value)

    def on_select_assets(self, assets):
        '''
        Triggered when select action is clicked on the asset_table_view.
        '''
        self.select_assets.emit(assets)

    def on_remove_assets(self, assets):
        '''
        Triggered when remove action is clicked on the asset_table_view.
        '''
        self.remove_assets.emit(assets)

    def on_update_assets(self, assets, plugin):
        '''
        Triggered when update action is clicked on the asset_table_view.
        '''
        self.update_assets.emit(assets, plugin)

    def on_load_assets(self, assets):
        '''
        Triggered when load action is clicked on the asset_table_view.
        '''
        self.load_assets.emit(assets)

    def on_unload_assets(self, assets):
        '''
        Triggered when unload action is clicked on the asset_table_view.
        '''
        self.unload_assets.emit(assets)

    def set_asset_list(self, asset_entities_list):
        '''
        Sets the :obj:`asset_entities_list` with the given *asset_entities_list*
        '''
        self.asset_entities_list = asset_entities_list
        #self.asset_table_view.set_asset_list(self.asset_entities_list)