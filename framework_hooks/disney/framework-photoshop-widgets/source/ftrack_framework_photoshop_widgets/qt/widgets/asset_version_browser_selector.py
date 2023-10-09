# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_widget.widget import FrameworkWidget

from ftrack_qt.widgets.views import TableView
from ftrack_qt.widgets.delegate import AssetVersionComboBoxDelegate


# TODO: review and docstring this code
class AssetVersionBrowserWidget(FrameworkWidget, TableView):
    '''Main class to represent a context widget on a publish process.'''

    name = 'asset_version_browser_selector'
    ui_type = 'qt'

    @property
    def selected_assets(self):
        return self._on_select_items()

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
            'date': 'date',
        }

        self._version_cb_delegate = None

        TableView.__init__(self, column_mapping=column_mapping, parent=parent)
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

    def build(self):
        '''
        Override build method of TableView to propagate a delegate item
        in the versions column
        '''
        super(AssetVersionBrowserWidget, self).build()
        self._version_cb_delegate = AssetVersionComboBoxDelegate(self)
        version_column_index = self.table_model.headers.index('version')
        self.setItemDelegateForColumn(
            version_column_index, self._version_cb_delegate
        )
        self.table_model.set_editable_column(version_column_index)

    def post_build(self):
        '''Perform post-construction operations.'''
        self._version_cb_delegate.index_changed.connect(
            self._on_asset_change_version
        )

    def _on_asset_change_version(self, index, value):
        self.table_model.data_items[index.row()] = value

    def fetch_asset_versions(self):
        self.plugin_context_data = {'context_id': self.context_id}
        self.run_plugin_method('run')

    def run_plugin_callback(self, plugin_info):
        # Check the result of the desired method
        if plugin_info['plugin_widget_id'] != self.id:
            return

        if (
                plugin_info['plugin_method'] == 'run'
                and plugin_info['plugin_method_result']
        ):
            self.set_data_items(plugin_info['plugin_method_result'])

    def _on_select_items(self):
        '''Updates the option dictionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        selected_asset_versions = super(
            AssetVersionBrowserWidget, self
        )._on_select_items()
        if not selected_asset_versions:
            return False
        asset_versions = []
        for selected_asset_version in selected_asset_versions:
            id = selected_asset_version['id']
            # TODO: to be implemented as option of the widget,
            #  be able to select the component.
            component = 'snapshot'
            asset_version_dict = {
                'asset_version_id': id,
                'component_name': component,
            }
            asset_versions.append(asset_version_dict)

        self.set_plugin_option('asset_versions', asset_versions)
        return asset_versions

    def fetch(self):
        self.fetch_asset_versions()
