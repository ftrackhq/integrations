# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

from ftrack_utils.framework.config.tool import get_groups
from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.progress import ProgressWidget
from ftrack_qt.utils.widget import build_progress_data


class LoaderDialog(BaseContextDialog):
    """Default Framework Loader dialog"""

    name = "framework_loader_dialog"
    tool_config_type_filter = ["loader"]
    ui_type = "qt"
    run_button_title = "LOAD"

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
        """
        Initialize Loader dialog.

        *event_manager*: instance of
        :class:`~ftrack_framework_core.event.EventManager`
        *client_id*: Id of the client that initializes the current dialog
        *connect_methods_callback*: Client callback method for the dialog to be
        able to execute client methods.
        *connect_setter_property_callback*: Client callback property setter for
        the dialog to be able to read client properties.
        *connect_getter_property_callback*: Client callback property getter for
        the dialog to be able to write client properties.
        *dialog_options*: Dictionary of arguments passed on to configure the
        current dialog.
        """
        self._scroll_area = None
        self._scroll_area_widget = None
        self._progress_widget = None
        self._component_selector = None
        self._load_options_widget = None

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
        # Select the desired tool_config
        tool_config_message = None
        if self.filtered_tool_configs.get("loader"):
            if len(self.tool_config_names or []) != 1:
                tool_config_message = (
                    "One(1) tool config name must be supplied to loader!"
                )
            else:
                tool_config_name = self.tool_config_names[0]
                for tool_config in self.filtered_tool_configs["loader"]:
                    if (
                        tool_config.get("name", "").lower()
                        == tool_config_name.lower()
                    ):
                        self.logger.debug(
                            f"Using tool config {tool_config_name}"
                        )
                        if self.tool_config != tool_config:
                            try:
                                self.tool_config = tool_config
                            except Exception as error:
                                tool_config_message = error
                                break
                            self._progress_widget = ProgressWidget(
                                "load", build_progress_data(tool_config)
                            )
                            self.header.set_widget(
                                self._progress_widget.status_widget
                            )
                            self.overlay_layout.addWidget(
                                self._progress_widget.overlay_widget
                            )
                        break
                if not self.tool_config and not tool_config_message:
                    tool_config_message = (
                        f'Could not find tool config: "{tool_config_name}"'
                    )
        else:
            tool_config_message = "No loader tool configs available!"

        if tool_config_message:
            self.logger.warning(tool_config_message)
            label_widget = QtWidgets.QLabel(f"{tool_config_message}")
            label_widget.setProperty("warning", True)
            self.tool_widget.layout().addWidget(label_widget)
            self.run_button.setEnabled(False)
            return

        # Build component selector widget
        self._build_component_selector()

        # Build load options widget
        self._build_load_options_widget()

    def _build_component_selector(self):
        """Build widget for selecting components to load"""
        component_groups = get_groups(
            self.tool_config, filters={"tags": ["component"]}
        )
        if not component_groups:
            return

        group_box = QtWidgets.QGroupBox("Components")
        layout = QtWidgets.QVBoxLayout()

        for _group in component_groups:
            group_options = _group.get("options") or {}
            component_name = group_options.get("component", "")
            file_formats = _group.get("file_formats", [])
            optional = _group.get("optional", False)
            enabled = _group.get("enabled", True)

            checkbox = QtWidgets.QCheckBox(component_name)
            checkbox.setChecked(enabled)
            checkbox.toggled.connect(
                partial(self._on_component_toggled, _group)
            )

            formats_str = ", ".join(file_formats) if file_formats else "any"
            description = f"  ({formats_str})"
            if optional:
                description += " - optional"
            label = QtWidgets.QLabel(description)
            # QLabel[secondary='true'] is styled by the theme as muted gray.
            label.setProperty("secondary", True)

            layout.addWidget(checkbox)
            layout.addWidget(label)

        layout.addStretch()
        group_box.setLayout(layout)
        self.tool_widget.layout().addWidget(group_box)

    def _on_component_toggled(self, group_config, checked):
        """Persist component enabled state so execute_engine skips it."""
        self.set_tool_config_option(
            {"enabled": checked}, group_config["reference"]
        )
        group_config["enabled"] = checked

    def _build_load_options_widget(self):
        """Build widget for load options"""
        group_box = QtWidgets.QGroupBox("Load Options")
        layout = QtWidgets.QFormLayout()

        # Simple text input for custom options (can be expanded later)
        self._load_mode_input = QtWidgets.QLineEdit()
        self._load_mode_input.setPlaceholderText(
            "e.g. reference, import, Read, ReadGeo2"
        )
        layout.addRow("Load Mode:", self._load_mode_input)

        group_box.setLayout(layout)
        self.tool_widget.layout().addWidget(group_box)

    def post_build_ui(self):
        pass
