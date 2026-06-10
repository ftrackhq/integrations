# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    from PySide2 import QtCore, QtWidgets

from ftrack_framework_qt.widgets import BaseWidget
from ftrack_qt.widgets.selectors import OpenAssetSelector
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class AssetVersionSelectorWidget(BaseWidget):
    """Main class to represent an asset version selector widget."""

    name = "asset_version_selector"
    ui_type = "qt"

    # Emitted when the user picks a version. Carries the version dict and
    # its parent asset_id so dialogs (e.g. the Loader) can drive downstream
    # state without going through plugin options.
    asset_version_selected = QtCore.Signal(object, str)

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
        """Initialize PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        """
        self._title_label = None
        self._label = None
        self._asset_version_selector = None
        self._show_all = None

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
        """Set up the main layout for the widget."""
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build_ui(self):
        """Build the user interface for the widget."""
        self._title_label = QtWidgets.QLabel("Assets")

        self._label = QtWidgets.QLabel()
        self._label.setProperty("secondary", True)
        self._label.setWordWrap(True)

        # Show assets from AssetBuild
        self._show_all = QtWidgets.QCheckBox("Show all assets")
        self._show_all.setChecked(False)

        self._asset_version_selector = OpenAssetSelector()

        self.layout().addWidget(self._title_label)
        self.layout().addWidget(self._label)
        self.layout().addWidget(self._show_all)
        self.layout().addWidget(self._asset_version_selector)

    def post_build_ui(self):
        """Perform post-construction operations."""
        self._asset_version_selector.assets_added.connect(
            self._on_assets_added
        )
        self._asset_version_selector.version_changed.connect(
            self._on_version_changed_callback
        )
        self._asset_version_selector.selected_item_changed.connect(
            self._on_selected_item_changed_callback
        )
        self._show_all.stateChanged.connect(self.populate)

    def populate(self):
        """Fetch info from plugin to populate the widget"""
        self.query_assets()

    def query_assets(self):
        """Query assets based on the context and asset type."""
        # group_config is absent when the widget is mounted at the dialog
        # level (e.g. the Loader's top-level picker). Treat absent component
        # as "no component filter". Likewise, plugin_config['options'] may
        # be omitted in YAML if no fields are needed.
        plugin_options = (self.plugin_config or {}).get("options") or {}
        group_options = (getattr(self, "group_config", None) or {}).get(
            "options"
        ) or {}
        payload = {
            "context_id": self.context_id,
            "asset_type_name": plugin_options.get("asset_type_name"),
            "component": group_options.get("component"),
            "show_all": self._show_all.isChecked(),
        }
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        """Handle the result of the UI hook."""
        super(AssetVersionSelectorWidget, self).ui_hook_callback(
            ui_hook_result
        )
        self._asset_version_selector.set_assets(ui_hook_result["assets"])

    def _on_assets_added(self, assets):
        """Handle the addition of assets to the selector."""
        if len(assets or []) > 0:
            self._label.setText(
                f'We found {len(assets)} asset{"s" if len(assets) > 1 else ""} '
                'published related to this task and its parent. Choose asset'
            )
        else:
            self._label.setText("No assets found.")

    def _on_version_changed_callback(self, version):
        """Handle the change of selected version."""
        self.set_plugin_option("asset_version_id", version["id"])

    def _on_selected_item_changed_callback(self, version, asset_id):
        """Handle the change of selected item."""
        self.set_plugin_option("asset_version_id", version.get("id"))
        self.set_plugin_option("asset_id", asset_id)
        self.asset_version_selected.emit(version, asset_id)
