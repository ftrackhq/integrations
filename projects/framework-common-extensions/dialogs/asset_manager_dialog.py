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
    """Default Framework Asset Manager dialog"""

    name = "framework_asset_manager_dialog"
    tool_config_type_filter = ["asset_manager"]
    run_button_title = "DISCOVER"
    ui_type = "qt"

    # Names of the per-action tool configs the dialog dispatches to from
    # the context-menu actions. Looked up by name in the registered
    # ``asset_manager`` tool configs and stored on ``_action_configs``.
    ACTION_CONFIG_NAMES = {
        "select": "nuke-asset-manager-select",
        "load": "nuke-asset-manager-load",
        "update": "nuke-asset-manager-update",
        "unload": "nuke-asset-manager-unload",
        "remove": "nuke-asset-manager-remove",
        "change_version": "nuke-asset-manager-change-version",
    }

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
        self._asset_list_model = None
        self._asset_manager_widget = None
        self._apply_button = None
        self._action_configs = {}

        super(AssetManagerDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )
        self.setWindowTitle("ftrack Asset Manager")
        # The base dialog defaults to a narrow size that clips the row
        # content (asset name + version + user + component all on one
        # line). Open with a width that fits comfortably and a bit more
        # height so a handful of rows are visible without scrolling.
        self.resize(QtCore.QSize(900, 800))

    def post_build(self):
        """Re-layout the bottom row so DISCOVER and APPLY CHANGES sit
        side-by-side. The base class adds the run button vertically to
        ``main_layout``; pull it back out, wrap it with the Apply button,
        and re-insert the pair at the bottom."""
        super(AssetManagerDialog, self).post_build()

        self._apply_button = QtWidgets.QPushButton("APPLY CHANGES")
        self._apply_button.setEnabled(False)
        self._apply_button.clicked.connect(self._on_apply_clicked)

        self.main_layout.removeWidget(self._run_button)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(6)
        button_row.addWidget(self._run_button)
        button_row.addWidget(self._apply_button)

        self.main_layout.addLayout(button_row)

    def pre_build_ui(self):
        pass

    def build_ui(self):
        # Select the desired tool_config
        tool_config_message = None
        if self.filtered_tool_configs.get("asset_manager"):
            if len(self.tool_config_names or []) != 1:
                tool_config_message = (
                    "One(1) tool config name must be supplied to "
                    "asset manager!"
                )
            else:
                tool_config_name = self.tool_config_names[0]
                for tool_config in self.filtered_tool_configs["asset_manager"]:
                    if (
                        tool_config.get("name", "").lower()
                        == tool_config_name.lower()
                    ):
                        self.logger.debug(
                            f"Using tool config {tool_config_name}"
                        )
                        if self.tool_config != tool_config:
                            self.tool_config = tool_config
                        break
                if not self.tool_config and not tool_config_message:
                    tool_config_message = (
                        f'Could not find tool config: "{tool_config_name}"'
                    )
        else:
            tool_config_message = "No asset_manager tool configs available!"

        if not self.tool_config:
            self.logger.warning(tool_config_message)
            label_widget = QtWidgets.QLabel(f"{tool_config_message}")
            label_widget.setProperty("warning", True)
            self.tool_widget.layout().addWidget(label_widget)
            self.run_button.setEnabled(False)
            if self._apply_button is not None:
                self._apply_button.setEnabled(False)
            return

        # Index every registered asset_manager tool config by name so the
        # context-menu / Apply-Changes / select-in-scene handlers can pick
        # the right action config to dispatch to.
        self._action_configs = {}
        for cfg in self.filtered_tool_configs.get("asset_manager", []):
            cfg_name = (cfg.get("name") or "").lower()
            if cfg_name:
                self._action_configs[cfg_name] = cfg

        self._asset_list_model = AssetListModel(self.event_manager)

        self._asset_manager_widget = AssetManagerWidget(
            self.event_manager, self._asset_list_model
        )

        self.tool_widget.layout().addWidget(self._asset_manager_widget)

        # Action signals from the widget to engine methods
        self._asset_manager_widget.selectAssets.connect(self._on_select_assets)
        self._asset_manager_widget.removeAssets.connect(self._on_remove_assets)
        self._asset_manager_widget.loadAssets.connect(self._on_load_assets)
        self._asset_manager_widget.unloadAssets.connect(self._on_unload_assets)
        self._asset_manager_widget.updateAssets.connect(self._on_update_assets)
        self._asset_manager_widget.changeAssetVersion.connect(
            self._on_change_asset_version
        )
        self._asset_manager_widget.selectInScene.connect(
            self._on_select_in_scene
        )
        self._asset_manager_widget.pendingChanged.connect(
            self._on_pending_changed
        )

    def post_build_ui(self):
        pass

    # ------------------------------------------------------------------
    # Per-action tool-config dispatch
    # ------------------------------------------------------------------

    def _dispatch_action(self, action_key, assets, extra_options=None):
        """Run the per-action tool config named by ``ACTION_CONFIG_NAMES``,
        passing ``assets`` (a list of FtrackAssetInfo dicts) and any
        ``extra_options`` via top-level tool-config options. The action
        plugin reads them from ``self.options['assets']``."""
        config_name = self.ACTION_CONFIG_NAMES.get(action_key)
        if not config_name:
            self.logger.warning(
                "AssetManagerDialog: no action config name for '{}'".format(
                    action_key
                )
            )
            return
        cfg = self._action_configs.get(config_name.lower())
        if not cfg:
            self.logger.warning(
                "AssetManagerDialog: action config '{}' not registered. "
                "Make sure the corresponding tool-config YAML is deployed.".format(
                    config_name
                )
            )
            return

        options = {"assets": list(assets or [])}
        if extra_options:
            options.update(extra_options)

        # Bypass Dialog.set_tool_config_option (hardcoded to self.tool_config)
        # and target the action config directly via the client API.
        self.client_method_connection(
            "set_config_options",
            arguments={
                "tool_config_reference": cfg["reference"],
                "options": options,
            },
        )
        self.run_tool_config(cfg["reference"])

    def _on_select_assets(self, asset_info_list, plugin):
        self._dispatch_action("select", asset_info_list)

    def _on_remove_assets(self, asset_info_list, plugin):
        self._dispatch_action("remove", asset_info_list)

    def _on_load_assets(self, asset_info_list, plugin):
        self._dispatch_action("load", asset_info_list)

    def _on_unload_assets(self, asset_info_list, plugin):
        self._dispatch_action("unload", asset_info_list)

    def _on_update_assets(self, asset_info_list, plugin):
        self._dispatch_action("update", asset_info_list)

    def _on_change_asset_version(self, asset_info, version_entity):
        """Single-row version change. Routes through the APPLY CHANGES
        config so the same plugin handles both staged batches and
        immediate one-row updates."""
        pending_changes = [
            {
                "asset_info_id": asset_info.get("asset_info_id"),
                "new_version_id": version_entity.get("id"),
                "component_name": asset_info.get("component_name"),
            }
        ]
        self._dispatch_action(
            "change_version",
            assets=[asset_info],
            extra_options={"pending_changes": pending_changes},
        )

    def _on_select_in_scene(self, asset_info):
        """Single-row select-in-scene from the crosshair button."""
        self._dispatch_action("select", [asset_info])

    # ------------------------------------------------------------------
    # APPLY CHANGES button
    # ------------------------------------------------------------------

    def _on_pending_changed(self, count):
        if self._apply_button is None:
            return
        if count > 0:
            self._apply_button.setText("APPLY CHANGES ({})".format(count))
            self._apply_button.setEnabled(True)
        else:
            self._apply_button.setText("APPLY CHANGES")
            self._apply_button.setEnabled(False)

    def _on_apply_clicked(self):
        """Walk pending rows, group by action type, dispatch one
        tool-config per type that has any rows. Each dispatch is its own
        plugin chain (the action plugin + a trailing scene_discover);
        consecutive scene_discover runs are cheap and the last one wins
        for ``store['versions']``, so the list refreshes correctly."""
        if self._asset_manager_widget is None:
            return
        pending = self._asset_manager_widget.pending_changes()
        if not pending:
            return

        version_assets = []
        version_changes = []
        load_assets = []
        unload_assets = []
        remove_assets = []

        for asset_info, action, data in pending:
            if action == "version" and data:
                version_assets.append(asset_info)
                version_changes.append(
                    {
                        "asset_info_id": asset_info.get("asset_info_id"),
                        "new_version_id": data.get("id"),
                        "component_name": asset_info.get("component_name"),
                    }
                )
            elif action == "load":
                load_assets.append(asset_info)
            elif action == "unload":
                unload_assets.append(asset_info)
            elif action == "remove":
                remove_assets.append(asset_info)

        if version_assets:
            self._dispatch_action(
                "change_version",
                assets=version_assets,
                extra_options={"pending_changes": version_changes},
            )
        if load_assets:
            self._dispatch_action("load", load_assets)
        if unload_assets:
            self._dispatch_action("unload", unload_assets)
        if remove_assets:
            self._dispatch_action("remove", remove_assets)

        self._asset_manager_widget.clear_pending_changes()

    # ------------------------------------------------------------------
    # Plugin callback: receive scene-discovery payload, enrich, render
    # ------------------------------------------------------------------

    def plugin_run_callback(self, log_item):
        """Receive plugin execution callbacks; render the asset list any
        time a plugin's store carries a 'versions' list. Last-writer wins,
        so a DCC-specific scene-discovery plugin appended to the chain
        (e.g. ``nuke.am_scene_discover``) overrides the resolver's
        ftrack-side suggestion with what's actually in the script.

        Before rendering, enrich each asset_info dict with display fields
        (thumbnail, user, date, file_type, available_versions) that the
        new ``AssetWidget`` row needs."""
        status = log_item.status or ""
        if not (
            isinstance(status, str) and status.lower().startswith("success")
        ):
            return
        store = log_item.store or {}
        if "versions" not in store or self._asset_manager_widget is None:
            return

        asset_infos = store["versions"] or []
        try:
            self._enrich_asset_infos(asset_infos)
        except Exception:
            # Enrichment is decorative — never block list rendering on it.
            self.logger.exception(
                "Failed to enrich asset infos with display fields"
            )

        self._asset_manager_widget.set_asset_list(asset_infos)

    def _enrich_asset_infos(self, asset_infos):
        """Annotate each AM scene-discovered ``FtrackAssetInfo`` with the
        display-only fields the row widget needs:
        ``thumbnail_url``, ``user_first_name``, ``user_last_name``,
        ``date``, ``file_type``, ``server_url`` and ``available_versions``.

        Issues at most two ftrack queries per refresh (one for currently
        loaded versions, one for the full per-asset version list), keyed on
        the discovered ``asset_id`` / ``version_id`` set."""
        if not asset_infos:
            return
        session = self.event_manager.session

        version_ids = sorted(
            {
                ai.get("version_id")
                for ai in asset_infos
                if ai.get("version_id")
            }
        )
        asset_ids = sorted(
            {ai.get("asset_id") for ai in asset_infos if ai.get("asset_id")}
        )

        loaded_by_version = {}
        if version_ids:
            quoted = ", ".join('"{}"'.format(vid) for vid in version_ids)
            loaded_query = (
                "select id, date, thumbnail_url, user.first_name, "
                "user.last_name, components.id, components.file_type "
                "from AssetVersion where id in ({})".format(quoted)
            )
            with session.auto_populating(False):
                for av in session.query(loaded_query).all():
                    file_type_by_component = {
                        c["id"]: c.get("file_type") for c in av["components"]
                    }
                    loaded_by_version[av["id"]] = {
                        "thumbnail_url": (
                            av["thumbnail_url"]["url"]
                            if av.get("thumbnail_url")
                            else None
                        ),
                        "date": av["date"].strftime("%y-%m-%d %H:%M")
                        if av.get("date")
                        else "",
                        "user_first_name": av["user"]["first_name"]
                        if av.get("user")
                        else "",
                        "user_last_name": av["user"]["last_name"]
                        if av.get("user")
                        else "",
                        "file_type_by_component": file_type_by_component,
                    }

        versions_by_asset = {}
        if asset_ids:
            quoted = ", ".join('"{}"'.format(aid) for aid in asset_ids)
            versions_query = (
                "select asset_id, id, date, version, is_latest_version, "
                "thumbnail_url, user.first_name, user.last_name, "
                "asset.type.short, components.id, components.name, "
                "components.file_type "
                "from AssetVersion where asset_id in ({})".format(quoted)
            )
            with session.auto_populating(False):
                for av in session.query(versions_query).all():
                    versions_by_asset.setdefault(av["asset_id"], []).append(
                        {
                            "id": av["id"],
                            "version": av["version"],
                            "date": av["date"].strftime("%y-%m-%d %H:%M")
                            if av.get("date")
                            else "",
                            "is_latest_version": av["is_latest_version"],
                            "thumbnail": (
                                av["thumbnail_url"]["url"]
                                if av.get("thumbnail_url")
                                else None
                            ),
                            "user_first_name": av["user"]["first_name"]
                            if av.get("user")
                            else "",
                            "user_last_name": av["user"]["last_name"]
                            if av.get("user")
                            else "",
                            "asset_type": av["asset"]["type"]["short"]
                            if av.get("asset") and av["asset"].get("type")
                            else None,
                            "components": [
                                {
                                    "id": c["id"],
                                    "name": c["name"],
                                    "file_type": c.get("file_type"),
                                }
                                for c in av["components"]
                            ],
                        }
                    )

        server_url = session.server_url

        for asset_info in asset_infos:
            asset_info["server_url"] = server_url

            loaded = loaded_by_version.get(asset_info.get("version_id"))
            if loaded:
                asset_info["thumbnail_url"] = loaded["thumbnail_url"]
                asset_info["date"] = loaded["date"]
                asset_info["user_first_name"] = loaded["user_first_name"]
                asset_info["user_last_name"] = loaded["user_last_name"]
                asset_info["file_type"] = loaded["file_type_by_component"].get(
                    asset_info.get("component_id")
                )

            asset_info["available_versions"] = versions_by_asset.get(
                asset_info.get("asset_id"), []
            )

    def closeEvent(self, event):
        if self._asset_manager_widget and hasattr(
            self._asset_manager_widget, "cleanup"
        ):
            self._asset_manager_widget.cleanup()
        super(AssetManagerDialog, self).closeEvent(event)
