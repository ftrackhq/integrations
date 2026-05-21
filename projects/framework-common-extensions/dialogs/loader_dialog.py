# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

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

        if tool_config_message:
            self.show_config_error(tool_config_message)
            return

        # Build component selector widget
        self._build_component_selector()

        # Build load options widget
        self._build_load_options_widget()

    def _build_component_selector(self):
        """Build widget for selecting components to load"""
        components = self.tool_config.get("components", [])

        if not components:
            return

        # Create group box for components
        group_box = QtWidgets.QGroupBox("Components")
        layout = QtWidgets.QVBoxLayout()

        self._component_checkboxes = {}

        for component_config in components:
            component_name = component_config.get("name")
            file_formats = component_config.get("file_formats", [])
            optional = component_config.get("optional", False)
            selected = component_config.get("selected", True)

            # Create checkbox
            checkbox = QtWidgets.QCheckBox(component_name)
            checkbox.setChecked(selected)

            # Add description
            formats_str = ", ".join(file_formats) if file_formats else "any"
            description = f"  ({formats_str})"
            if optional:
                description += " - optional"

            label = QtWidgets.QLabel(description)
            label.setStyleSheet("color: gray; margin-left: 20px;")

            # Add to layout
            layout.addWidget(checkbox)
            layout.addWidget(label)

            self._component_checkboxes[component_name] = checkbox

        layout.addStretch()
        group_box.setLayout(layout)

        self.content_layout.addWidget(group_box)

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
        self.content_layout.addWidget(group_box)

    def post_build_ui(self):
        pass

    def run(self):
        """Execute loader pipeline"""
        # Get selected components
        selected_components = []
        if hasattr(self, "_component_checkboxes"):
            selected_components = [
                name
                for name, checkbox in self._component_checkboxes.items()
                if checkbox.isChecked()
            ]

        if not selected_components:
            self.logger.warning("No components selected!")
            return

        # Get load mode
        load_mode = None
        if hasattr(self, "_load_mode_input"):
            load_mode = self._load_mode_input.text().strip()

        # Build options
        options = {}
        if load_mode:
            options["load_mode"] = load_mode

        # Get context from context selector
        context_data = {}
        if self.context_id:
            # Query ftrack for context to get version_id
            # For now, assume context_id IS the version_id
            # (This should be enhanced to query properly)
            context_data["version_id"] = self.context_id

        self.logger.info(
            f"Running loader with components: {selected_components}, "
            f"context: {self.context_id}, options: {options}"
        )

        # Call run method callback
        result = self._run_method(
            "run",
            {
                "method": "init_and_load",
                "tool_config": self.tool_config,
                "context_data": context_data,
                "selected_components": selected_components,
                "options": options,
            },
        )

        # Update progress
        if self._progress_widget and result:
            # Update progress based on results
            for component_name, component_result in result.get(
                "component_results", {}
            ).items():
                status = component_result.get("status", "unknown")
                self.logger.info(
                    f"Component {component_name} status: {status}"
                )

        return result

    def on_run_plugin_callback(self, plugin_run_result):
        """Callback when plugin is executed"""
        if self._progress_widget:
            self._progress_widget.update(plugin_run_result)


def register(api_object, **kw):
    """Register dialog to framework"""
    # Auto-registration handled by framework dialog discovery
    pass
