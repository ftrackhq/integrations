# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import time

from Qt import QtWidgets

from ftrack_framework_widget.widget import FrameworkWidget
from ftrack_qt.widgets.selectors import AssetSelector


class AssetVersionSelectorWidget(FrameworkWidget, QtWidgets.QWidget):
    """Main class to represent an asset version selector widget."""

    name = "assetversion_selector"
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
        """initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        """

        QtWidgets.QWidget.__init__(self, parent=parent)
        FrameworkWidget.__init__(
            self,
            event_manager,
            client_id,
            context_id,
            plugin_config,
            group_config,
            on_set_plugin_option,
            on_run_ui_hook,
            parent,
        )

        self._label = None
        self._assetversion_selector = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build(self):
        self._label = QtWidgets.QLabel()
        self._label.setObjectName('gray')
        self._label.setWordWrap(True)

        self._assetversion_selector = AssetSelector(
            AssetSelector.MODE_SELECT_ASSETVERSION,
            self._on_fetch_assets_callback,
            self.session,
            fetch_assetversions=self._on_fetch_assetversions_callback,
        )

        self.layout().addWidget(self._label)
        self.layout().addWidget(self._assetversion_selector)

    def post_build(self):
        """Perform post-construction operations."""
        self._assetversion_selector.assetsAdded.connect(self._on_assets_added)
        self._assetversion_selector.versionChanged.connect(
            self._on_version_changed_callback
        )
        # set context
        self.set_context()

    def set_context(self):
        self._assetversion_selector.reload()

    def _on_fetch_assets_callback(self):
        '''Return assets back to asset selector'''
        payload = {
            'context_id': self.context_id,
            'context_type': 'asset',
            'asset_type_name': self.plugin_config['options'].get(
                'asset_type_name'
            ),
        }
        return self.run_ui_hook(payload, await_result=True)

    def _on_fetch_assetversions_callback(self, asset_entity):
        '''Query ftrack for all version beneath *asset_entity*'''
        return []
        payload = {
            'context_id': self.context_id,
            'context_type': 'asset_version',
            'asset_id': asset_entity,
        }
        return self.run_ui_hook(payload, await_result=True)

    def _on_assets_added(self, assets):
        if len(assets or []) > 0:
            self._label.setText(
                'We found {} asset{} published '
                ' on this task. Choose version '
                'to open'.format(
                    len(assets),
                    's' if len(assets) > 1 else '',
                )
            )
        else:
            self._label.setText('<html><i>No assets found!<i></html>')

    def _on_version_changed_callback(self, assetversion_entity):
        component_name = self.group_config.get('options').get('component')
        self.set_plugin_option(
            'asset_versions',
            [
                {
                    'asset_version_id': assetversion_entity['id'],
                    'component_name': component_name,
                }
            ],
        )
