# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os.path

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_widget.widget import FrameworkWidget

from ftrack_qt.widgets.views import AssetTableView

# TODO: review and docstring this code
class AssetVersionBrowserWidget(FrameworkWidget, AssetTableView):
    '''Main class to represent a context widget on a publish process.'''

    name = 'asset_version_browser_collector'
    ui_type = 'qt'

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        dialog_connect_methods_callback,
        dialog_property_getter_connection_callback,
        parent=None,
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        column_mapping = {
            'name': ['asset', 'name'],
            'version': 'version',
            'date': 'date'
        }

        AssetTableView.__init__(self, column_mapping=column_mapping, parent=parent)
        FrameworkWidget.__init__(
            self,
            event_manager,
            client_id,
            context_id,
            plugin_config,
            dialog_connect_methods_callback,
            dialog_property_getter_connection_callback,
            parent=parent,
        )


    # def post_build(self):
    #     '''hook events'''
    #     self._file_browser.path_changed.connect(self._on_path_changed)

    def fetch_asset_versions(self):
        self.plugin_context_data = {'context_id': self.context_id}
        self.run_plugin_method('fetch')

    def run_plugin_callback(self, plugin_info):
        # Check is the result of the dessired method
        if not (
            plugin_info['plugin_widget_id'] == self.id
            and plugin_info['plugin_method'] == 'fetch'
        ):
            return
        if plugin_info['plugin_method_result']:
            self.set_data_items(plugin_info['plugin_method_result'])

    # def _on_path_changed(self, file_path):
    #     '''Updates the option dictionary with provided *asset_name* when
    #     asset_changed of asset_selector event is triggered'''
    #     self.set_plugin_option('folder_path', os.path.dirname(file_path))
    #     self.set_plugin_option('file_name', os.path.basename(file_path))
