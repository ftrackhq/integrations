# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets

from ftrack_framework_qt.widgets import BaseWidget
from ftrack_qt.widgets.selectors import OpenAssetSelector
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class AssetVersionSelectorWidget(BaseWidget):
    '''Main class to represent an asset version selector widget.'''

    name = "asset_version_selector"
    ui_type = "qt"

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        group_config,
        on_set_plugin_option,
        on_run_ui_hook,
        parent=None,
    ):
        '''Initialize PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._label = None
        self._asset_version_selector = None

        super(AssetVersionSelectorWidget, self).__init__(
            event_manager,
            client_id,
            context_id,
            plugin_config,
            group_config,
            on_set_plugin_option,
            on_run_ui_hook,
            parent,
        )

    def pre_build_ui(self):
        '''Set up the main layout for the widget.'''
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build_ui(self):
        '''Build the user interface for the widget.'''
        self._label = QtWidgets.QLabel()
        self._label.setObjectName('gray')
        self._label.setWordWrap(True)

        self._asset_version_selector = OpenAssetSelector()

        self.layout().addWidget(self._label)
        self.layout().addWidget(self._asset_version_selector)

    def post_build_ui(self):
        '''Perform post-construction operations.'''
        self._asset_version_selector.assets_added.connect(
            self._on_assets_added
        )
        self._asset_version_selector.version_changed.connect(
            self._on_version_changed_callback
        )
        self._asset_version_selector.selected_item_changed.connect(
            self._on_selected_item_changed_callback
        )

    def populate(self):
        '''Fetch info from plugin to populate the widget'''
        self.query_assets()

    def query_assets(self):
        '''Query assets based on the context and asset type.'''
        payload = {
            'context_id': self.context_id,
            'asset_type_name': self.plugin_config['options'].get(
                'asset_type_name'
            ),
        }
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Handle the result of the UI hook.'''
        super(AssetVersionSelectorWidget, self).ui_hook_callback(
            ui_hook_result
        )
        self._asset_version_selector.set_assets(ui_hook_result['assets'])

    def _on_assets_added(self, assets):
        '''Handle the addition of assets to the selector.'''
        if len(assets or []) > 0:
            self._label.setText(
                'We found {} asset{} published on this task. '
                'Choose asset'.format(
                    len(assets),
                    's' if len(assets) > 1 else '',
                )
            )
        else:
            self._label.setText('<html><i>No assets found!<i></html>')

    def _on_version_changed_callback(self, version):
        '''Handle the change of selected version.'''
        self.set_plugin_option('asset_version_id', version['id'])

    def _on_selected_item_changed_callback(self, version, asset_id):
        '''Handle the change of selected item.'''
        self.set_plugin_option('asset_version_id', version.get('id'))
        self.set_plugin_option('asset_id', asset_id)
