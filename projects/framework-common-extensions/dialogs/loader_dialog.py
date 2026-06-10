# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

from ftrack_utils.framework.config.tool import get_groups, get_plugins
from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.progress import ProgressWidget
from ftrack_qt.utils.widget import build_progress_data


class LoaderDialog(BaseContextDialog):
    """Default Framework Loader dialog.

    Flow:
    1. Mount a single ``asset_version_selector`` widget (driven by
       ``common.loader_asset_picker`` declared in the YAML).
    2. On selection the dialog reads the version's components, checks each
       for a non-``ftrack.server`` location, resolves a per-component
       **filetype** (user pick → ``component.file_type`` → YAML
       ``component_filetype_defaults`` → None), and matches each row to a
       tool-config component group whose ``options.file_types`` list
       contains that filetype.
    3. Rows are rendered with a checkbox + filetype dropdown. Server-only
       components and components with no matching importer render disabled
       but the dropdown stays interactive so the user can pick a different
       filetype that *does* have an importer wired.
    4. Toggling a checkbox writes the full group state
       (``{enabled, asset_version_id, component}``) to the matching group's
       reference so the engine can dispatch the right importer at run
       time.
    """

    name = "framework_loader_dialog"
    tool_config_type_filter = ["loader"]
    ui_type = "qt"
    run_button_title = "LOAD"

    WILDCARD_FILETYPE = "*"

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
        self._progress_widget = None
        self._picker_widget = None
        self._asset_type_label = None
        self._components_group = None
        self._components_layout = None
        self._components_placeholder = None
        self._component_rows = []
        self._selected_asset_version_id = None
        self._selected_asset_id = None
        self._selected_asset_type = None
        self._selected_components = []
        # Per-component manual filetype picks made via the row dropdown.
        # Cleared whenever a new AssetVersion is selected.
        self._manual_file_types = {}
        # Cached union of all file_types declared on the loader's groups.
        self._file_types_cache = None
        # Tracks the full group-state dict per group reference, so each
        # set_tool_config_option call writes the *complete* state — the
        # call assigns, not merges (client/__init__.py:540-546).
        self._group_state = {}

        super(LoaderDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )
        self.resize(500, 600)
        self.setWindowTitle("ftrack Loader")

    def pre_build_ui(self):
        pass

    def build_ui(self):
        # Reset per-build state.
        self._picker_widget = None
        self._asset_type_label = None
        self._components_group = None
        self._components_layout = None
        self._components_placeholder = None
        self._component_rows = []
        self._selected_asset_version_id = None
        self._selected_asset_id = None
        self._selected_asset_type = None
        self._selected_components = []
        self._manual_file_types = {}
        self._file_types_cache = None
        self._group_state = {}

        tool_config_message = self._resolve_tool_config()
        if tool_config_message:
            self.logger.warning(tool_config_message)
            label_widget = QtWidgets.QLabel(f"{tool_config_message}")
            label_widget.setProperty("warning", True)
            self.tool_widget.layout().addWidget(label_widget)
            self.run_button.setEnabled(False)
            return

        self._mount_picker_widget()
        self._build_components_container()
        self._build_load_options_widget()
        self._update_run_button_state()

    def _resolve_tool_config(self):
        """Pick the requested tool config from the filtered set. Returns an
        error message on failure, or None on success."""
        if not self.filtered_tool_configs.get("loader"):
            return "No loader tool configs available!"
        if len(self.tool_config_names or []) != 1:
            return "One(1) tool config name must be supplied to loader!"

        tool_config_name = self.tool_config_names[0]
        for tool_config in self.filtered_tool_configs["loader"]:
            if tool_config.get("name", "").lower() == tool_config_name.lower():
                self.logger.debug(f"Using tool config {tool_config_name}")
                if self.tool_config != tool_config:
                    try:
                        self.tool_config = tool_config
                    except Exception as error:
                        return str(error)
                    self._progress_widget = ProgressWidget(
                        "load", build_progress_data(tool_config)
                    )
                    self.header.set_widget(self._progress_widget.status_widget)
                    self.overlay_layout.addWidget(
                        self._progress_widget.overlay_widget
                    )
                return None
        return f'Could not find tool config: "{tool_config_name}"'

    def _mount_picker_widget(self):
        """Init the top-level asset/version picker widget from the YAML."""
        context_plugins = get_plugins(
            self.tool_config, filters={"tags": ["context"]}
        )
        for plugin_config in context_plugins:
            if not plugin_config.get("ui"):
                continue
            self._picker_widget = self.init_framework_widget(plugin_config)
            self._picker_widget.asset_version_selected.connect(
                self._on_asset_version_selected
            )
            self.tool_widget.layout().addWidget(self._picker_widget)
            break

    def _build_components_container(self):
        """Create the QGroupBox that will hold the component rows."""
        self._components_group = QtWidgets.QGroupBox("Components")
        self._components_layout = QtWidgets.QVBoxLayout()
        self._components_group.setLayout(self._components_layout)
        self._asset_type_label = QtWidgets.QLabel("")
        self._asset_type_label.setProperty("secondary", True)
        self._asset_type_label.hide()
        self._components_layout.addWidget(self._asset_type_label)
        self._components_placeholder = QtWidgets.QLabel(
            "Select an asset version to choose components."
        )
        self._components_placeholder.setProperty("secondary", True)
        self._components_layout.addWidget(self._components_placeholder)
        self.tool_widget.layout().addWidget(self._components_group)

    def _build_load_options_widget(self):
        """Render a Load Options group only when the tool config declares a
        non-empty ``load_modes`` list. The first entry is the default; the
        picked value is pushed to top-level tool_config_options so the
        engine merges it into every plugin's ``self.options`` as
        ``load_mode``."""
        load_modes = self.tool_config.get("load_modes") or []
        if not load_modes:
            return
        group_box = QtWidgets.QGroupBox("Load Options")
        layout = QtWidgets.QFormLayout()
        combo = QtWidgets.QComboBox()
        for mode in load_modes:
            combo.addItem(mode, mode)
        combo.setCurrentIndex(0)
        layout.addRow("Load Mode:", combo)
        group_box.setLayout(layout)
        self.tool_widget.layout().addWidget(group_box)
        # Push the default once so the first LOAD always carries a value,
        # then keep it in sync with user changes.
        self.set_tool_config_option({"load_mode": load_modes[0]})
        combo.currentIndexChanged.connect(
            lambda _idx, c=combo: self.set_tool_config_option(
                {"load_mode": c.currentData()}
            )
        )

    def post_build_ui(self):
        pass

    # ------------------------------------------------------------------
    # Picker selection → component row rebuild
    # ------------------------------------------------------------------

    def _on_asset_version_selected(self, version, asset_id):
        """Called when the picker emits a version selection."""
        if not version:
            return
        self._selected_asset_version_id = version.get("id")
        self._selected_asset_id = asset_id
        self._selected_asset_type = self._extract_asset_type(version)
        self._selected_components = version.get("components", []) or []
        self._manual_file_types = {}
        self._rebuild_component_rows()

    @staticmethod
    def _extract_asset_type(version):
        """Pull the AssetVersion's asset_type short code from the picker
        payload. The picker populates ``asset.type.short`` via the version
        dict; if absent, fall back to None and let resolution chain handle
        it."""
        if not isinstance(version, dict):
            return None
        # The picker doesn't currently expose asset_type explicitly; the
        # dialog reads it from the version dict if present, otherwise None.
        # component_filetype_defaults entries scoped to a specific
        # asset_type simply won't match — defaults of None are fine.
        return version.get("asset_type")

    def _clear_component_rows(self):
        for row in self._component_rows:
            row.setParent(None)
            row.deleteLater()
        self._component_rows = []

    def _rebuild_component_rows(self):
        """Render one row per component on the selected version."""
        self._clear_component_rows()

        # Reset every component group to disabled. We'll re-enable only
        # those whose row ends up checked.
        for group in get_groups(
            self.tool_config, filters={"tags": ["component"]}
        ):
            self._reset_group_state(group)

        if not self._selected_components:
            self._asset_type_label.hide()
            self._components_placeholder.setText(
                "Selected version has no components."
            )
            self._components_placeholder.show()
            self._update_run_button_state()
            return

        if self._selected_asset_type:
            self._asset_type_label.setText(
                f'Loading components from a "{self._selected_asset_type}" '
                f"asset."
            )
            self._asset_type_label.show()
        else:
            self._asset_type_label.hide()
        self._components_placeholder.hide()

        for component in self._selected_components:
            row = self._build_component_row(component)
            self._component_rows.append(row)
            self._components_layout.addWidget(row)

        self._update_run_button_state()

    def _build_component_row(self, component):
        """Build one row for a component on the selected version."""
        container = QtWidgets.QFrame()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)

        component_name = component["name"]
        is_loadable = self._is_component_loadable(component)
        file_type = self._resolve_file_type(component_name, component)
        matching_group = (
            self._find_group_for_filetype(file_type) if file_type else None
        )

        checkbox = QtWidgets.QCheckBox(component_name)
        # Stash data on the row widget so _on_component_checkbox_toggled and
        # _on_file_type_picked can recover state without walking the tree.
        container.setProperty("component_name", component_name)
        layout.addWidget(checkbox)
        layout.addStretch()

        # Filetype dropdown — always a QComboBox so the user can override
        # at any time (recovery from "no importer wired" and consistency
        # across states).
        ft_combo = QtWidgets.QComboBox()
        ft_combo.addItem("(select filetype…)", None)
        all_file_types = self._get_all_file_types()
        current_idx = 0
        for idx, ft in enumerate(all_file_types):
            ft_combo.addItem(ft, ft)
            if file_type and self._normalize_extension(
                ft
            ) == self._normalize_extension(file_type):
                current_idx = idx + 1
        # If the resolved file_type isn't in the loader's known set, still
        # show it so the user sees what was auto-detected.
        if file_type and self._normalize_extension(file_type) not in [
            self._normalize_extension(ft) for ft in all_file_types
        ]:
            ft_combo.addItem(file_type, file_type)
            current_idx = ft_combo.count() - 1
        ft_combo.setCurrentIndex(current_idx)
        ft_combo.currentIndexChanged.connect(
            partial(self._on_file_type_picked, component_name)
        )
        layout.addWidget(ft_combo)

        # State machine.
        if not is_loadable:
            tooltip = (
                "Component is only available on the ftrack server location "
                "and cannot be loaded locally."
            )
            checkbox.setEnabled(False)
        elif not file_type:
            tooltip = "Select a filetype to enable loading."
            checkbox.setEnabled(False)
        elif not matching_group:
            tooltip = (
                f'No importer configured for filetype "{file_type}". '
                f"Pick another filetype to enable loading."
            )
            checkbox.setEnabled(False)
        else:
            tooltip = f'Will load as "{file_type}".'
            checkbox.setEnabled(True)
            checkbox.toggled.connect(
                partial(
                    self._on_component_checkbox_toggled,
                    matching_group,
                    component_name,
                )
            )

        container.setToolTip(tooltip)
        return container

    # ------------------------------------------------------------------
    # Per-row handlers
    # ------------------------------------------------------------------

    def _on_component_checkbox_toggled(
        self, group_config, component_name, checked
    ):
        """Toggle the matching group's enabled flag and push full state."""
        if checked:
            # Multi-component-same-group: if another row is already
            # claiming this group, uncheck it so the new selection wins.
            self._uncheck_other_rows_for_group(
                group_config, except_component=component_name
            )
            self._write_group_state(
                group_config,
                enabled=True,
                asset_version_id=self._selected_asset_version_id,
                component=component_name,
            )
        else:
            self._reset_group_state(group_config)
        self._update_run_button_state()

    def _uncheck_other_rows_for_group(self, group_config, except_component):
        """If any other row's checkbox is checked and resolves to the same
        group, uncheck it. The engine runs each group once, so two checked
        rows mapping to the same group would silently collide."""
        target_ref = group_config["reference"]
        for row in self._component_rows:
            other_name = row.property("component_name")
            if other_name == except_component:
                continue
            other_checkbox = row.findChild(QtWidgets.QCheckBox)
            if other_checkbox is None or not other_checkbox.isChecked():
                continue
            other_component = next(
                (
                    c
                    for c in self._selected_components
                    if c.get("name") == other_name
                ),
                None,
            )
            other_ft = self._resolve_file_type(other_name, other_component)
            other_group = (
                self._find_group_for_filetype(other_ft) if other_ft else None
            )
            if other_group and other_group["reference"] == target_ref:
                other_checkbox.blockSignals(True)
                other_checkbox.setChecked(False)
                other_checkbox.blockSignals(False)

    def _on_file_type_picked(self, component_name, _index):
        """User picked a filetype in a row dropdown. Re-render the rows
        with the new selection in effect."""
        for row in self._component_rows:
            if row.property("component_name") != component_name:
                continue
            combo = row.findChild(QtWidgets.QComboBox)
            if combo is None:
                continue
            picked = combo.currentData()
            if picked is None:
                self._manual_file_types.pop(component_name, None)
            else:
                self._manual_file_types[component_name] = picked
            break
        self._rebuild_component_rows()

    # ------------------------------------------------------------------
    # Resolution & matching
    # ------------------------------------------------------------------

    def _is_component_loadable(self, component):
        """True iff the component has at least one location that is not
        ``ftrack.server``."""
        location_names = component.get("location_names") or []
        return any(name != "ftrack.server" for name in location_names)

    def _resolve_file_type(self, component_name, component):
        """Resolution order (top wins):
        1. User's manual dropdown pick.
        2. ``component.file_type`` from ftrack (if non-empty).
        3. Top-level ``component_filetype_defaults`` matching the
           AssetVersion's asset_type + component name.
        4. None.
        """
        if component_name in self._manual_file_types:
            return self._manual_file_types[component_name]
        if component:
            ft = component.get("file_type")
            if ft:
                return self._normalize_extension(ft)
        defaults = self.tool_config.get("component_filetype_defaults") or []
        for entry in defaults:
            if entry.get("component") != component_name:
                continue
            if (
                entry.get("asset_type")
                and entry.get("asset_type") != self._selected_asset_type
            ):
                continue
            ft = entry.get("file_type")
            if ft:
                return self._normalize_extension(ft)
        return None

    def _find_group_for_filetype(self, file_type):
        """Return the first component group whose ``options.file_types``
        contains *file_type* (case-insensitive, leading-dot tolerated).
        A group with ``["*"]`` matches any non-empty filetype."""
        if not file_type:
            return None
        target = self._normalize_extension(file_type)
        for group in get_groups(
            self.tool_config, filters={"tags": ["component"]}
        ):
            options = group.get("options") or {}
            group_fts = options.get("file_types") or []
            if self.WILDCARD_FILETYPE in group_fts:
                return group
            normalized = [self._normalize_extension(ft) for ft in group_fts]
            if target in normalized:
                return group
        return None

    def _get_all_file_types(self):
        """Cached union of all file_types declared on the loader's groups,
        excluding the wildcard marker. Sorted for deterministic UI."""
        if self._file_types_cache is None:
            seen = set()
            ordered = []
            for group in get_groups(
                self.tool_config, filters={"tags": ["component"]}
            ):
                options = group.get("options") or {}
                for ft in options.get("file_types") or []:
                    if ft == self.WILDCARD_FILETYPE:
                        continue
                    norm = self._normalize_extension(ft)
                    if norm in seen:
                        continue
                    seen.add(norm)
                    ordered.append(norm)
            self._file_types_cache = sorted(ordered)
        return self._file_types_cache

    @staticmethod
    def _normalize_extension(value):
        """Lowercase + ensure leading dot so ``.ABC``, ``abc``, and ``.abc``
        all compare equal."""
        if not value:
            return ""
        value = value.lower()
        if not value.startswith(".") and value != "*":
            value = "." + value
        return value

    # ------------------------------------------------------------------
    # Group state pushdown
    # ------------------------------------------------------------------

    def _write_group_state(
        self, group_config, *, enabled, asset_version_id=None, component=None
    ):
        """Push the full state dict for a group to the client/engine.
        Because ``set_config_options`` assigns (not merges), every push
        must include every field the engine should see."""
        ref = group_config["reference"]
        state = {"enabled": enabled}
        if asset_version_id:
            state["asset_version_id"] = asset_version_id
        if component:
            state["component"] = component
        self._group_state[ref] = state
        self.set_tool_config_option(state, ref)
        group_config["enabled"] = enabled

    def _reset_group_state(self, group_config):
        """Clear any user_options the dialog wrote to this group, and mark
        it disabled in-memory."""
        ref = group_config["reference"]
        self._group_state.pop(ref, None)
        self.set_tool_config_option({"enabled": False}, ref)
        group_config["enabled"] = False

    def _update_run_button_state(self):
        any_checked = False
        for row in self._component_rows:
            checkbox = row.findChild(QtWidgets.QCheckBox)
            if (
                checkbox is not None
                and checkbox.isEnabled()
                and checkbox.isChecked()
            ):
                any_checked = True
                break
        self.run_button.setEnabled(any_checked)

    def closeEvent(self, event):
        if self._context_selector:
            self._context_selector.teardown()
        if self._progress_widget:
            self._progress_widget.teardown()
            self._progress_widget.deleteLater()
        super(LoaderDialog, self).closeEvent(event)
