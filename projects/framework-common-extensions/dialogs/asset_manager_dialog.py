# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_framework_asset_manager.ui.asset_manager_widget import (
    AssetManagerWidget,
)
from ftrack_framework_asset_manager.asset.asset_list_model import (
    AssetListModel,
)


class AssetManagerDialog(BaseContextDialog):
    '''Default Framework Asset Manager dialog'''

    name = 'framework_asset_manager_dialog'
    tool_config_type_filter = ['asset_manager']
    run_button_title = 'DISCOVER'
    ui_type = 'qt'

    def __init__(
        self,
        event_manager,
        client_id,
        connect_methods_callback,
        connect_setter_property_callback,
        connect_getter_property_callback,
        dialog_options,
        parent=None,
    ):
        '''
        Initialize Asset Manager dialog.
        *event_manager*: instance of
        :class:`~ftrack_framework_core.event.EventManager`
        *client_id*: Id of the client that initializes the current dialog
        *connect_methods_callback*: Client callback method for the dialog to be
        able to execute client methods.
        *connect_setter_property_callback*: Client callback property setter for
        the dialog to be able to read client properties.
        *connect_getter_property_callback*: Client callback property getter for
        the dialog to be able to write client properties.
        *dialog_options*: Dictionary of arguments passed to configure the
        current dialog.
        '''
        self._asset_list_model = None
        self._asset_manager_widget = None

        super(AssetManagerDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )
        self.setWindowTitle('ftrack Asset Manager')

    def pre_build_ui(self):
        '''Prepare the UI before building the main content'''
        pass

    def build_ui(self):
        '''Build the Asset Manager specific UI content'''
        # Create the AssetListModel
        self._asset_list_model = AssetListModel(self.event_manager)

        # Create the AssetManagerWidget
        self._asset_manager_widget = AssetManagerWidget(
            self.event_manager, self._asset_list_model
        )

        # Add the widget to the tool_widget layout
        self.tool_widget.layout().addWidget(self._asset_manager_widget)

        # Wire up signals from the widget to the engine
        self._asset_manager_widget.refresh.connect(self._on_refresh)
        self._asset_manager_widget.rebuild.connect(self._on_rebuild)
        self._asset_manager_widget.selectAssets.connect(self._on_select_assets)
        self._asset_manager_widget.removeAssets.connect(self._on_remove_assets)
        self._asset_manager_widget.loadAssets.connect(self._on_load_assets)
        self._asset_manager_widget.unloadAssets.connect(self._on_unload_assets)
        self._asset_manager_widget.updateAssets.connect(self._on_update_assets)
        self._asset_manager_widget.changeAssetVersion.connect(
            self._on_change_asset_version
        )

    def post_build_ui(self):
        '''Finalize the UI after building the main content'''
        pass

    def _on_refresh(self):
        '''Refresh the asset list from the model data'''
        self._asset_manager_widget._asset_list.rebuild()

    def _on_rebuild(self):
        '''Query DCC for scene assets and update the model'''
        self.run_tool_config(self.tool_config['reference'])

    def _on_select_assets(self, asset_info_list, plugin):
        '''Select assets in DCC'''
        self.run_tool_config(
            self.tool_config['reference'],
            method='select_assets',
            assets=asset_info_list,
        )

    def _on_remove_assets(self, asset_info_list, plugin):
        '''Remove assets from DCC'''
        self.run_tool_config(
            self.tool_config['reference'],
            method='remove_assets',
            assets=asset_info_list,
        )

    def _on_load_assets(self, asset_info_list, plugin):
        '''Load assets into DCC'''
        self.run_tool_config(
            self.tool_config['reference'],
            method='load_assets',
            assets=asset_info_list,
        )

    def _on_unload_assets(self, asset_info_list, plugin):
        '''Unload assets from DCC'''
        self.run_tool_config(
            self.tool_config['reference'],
            method='unload_assets',
            assets=asset_info_list,
        )

    def _on_update_assets(self, asset_info_list, plugin):
        '''Update DCC assets to latest version'''
        self.run_tool_config(
            self.tool_config['reference'],
            method='update_assets',
            assets=asset_info_list,
            plugin=plugin,
        )

    def _on_change_asset_version(self, asset_info, version_entity):
        '''Change the version of an asset'''
        self.run_tool_config(
            self.tool_config['reference'],
            method='change_version',
            assets=asset_info,
            options={'new_version_id': version_entity['id']},
        )

    def _on_run_button_clicked(self):
        '''(Override) Trigger asset discovery when run button is clicked'''
        self._on_rebuild()

    def closeEvent(self, event):
        '''(Override) Clean up widget subscriptions on close'''
        if self._asset_manager_widget:
            self._asset_manager_widget.cleanup()
        super(AssetManagerDialog, self).closeEvent(event)
