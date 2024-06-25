# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget


class MayaSceneLoadSelectorWidget(BaseWidget):
    '''Drop-down list to select the desired camera.'''

    name = 'maya_scene_load_selector'
    ui_type = 'qt'

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
        self._import_radio = None
        self._reference_radio = None
        self._button_group = None
        self._custom_namespace_checkbox = None
        self._custom_namespace_line_edit = None

        super(MayaSceneLoadSelectorWidget, self).__init__(
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
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build_ui(self):
        '''build function widgets.'''

        # Create radio buttons
        self._import_radio = QtWidgets.QRadioButton("Import")
        self._reference_radio = QtWidgets.QRadioButton("Reference")

        # Add radio buttons to button group to allow single selection
        self._button_group = QtWidgets.QButtonGroup()
        self._button_group.addButton(self._import_radio)
        self._button_group.addButton(self._reference_radio)

        # Add radio buttons to layout
        self.layout().addWidget(self._import_radio)
        self.layout().addWidget(self._reference_radio)

        # Create label for checkbox
        self.layout().addWidget(QtWidgets.QLabel("Options:"))

        h_layout = QtWidgets.QHBoxLayout()
        # Create checkbox for custom namespace
        self._custom_namespace_checkbox = QtWidgets.QCheckBox(
            "Enable Custom Namespace"
        )

        # Create line edit for custom namespace
        self._custom_namespace_line_edit = QtWidgets.QLineEdit()

        # Add checkbox to layout
        h_layout.addWidget(self._custom_namespace_checkbox)
        h_layout.addWidget(self._custom_namespace_line_edit)
        self.layout().addLayout(h_layout)

    def post_build_ui(self):
        '''hook events'''
        # Set default values
        if (
            self.plugin_config.get('options', {}).get('load_type')
            == 'reference'
        ):
            self._reference_radio.setChecked(True)
        elif (
            self.plugin_config.get('options', {}).get('load_type') == 'import'
        ):
            self._import_radio.setChecked(True)
        if self.plugin_config.get('options', {}).get('namespace'):
            self._custom_namespace_checkbox.setChecked(True)
            self._custom_namespace_line_edit.setText(
                self.plugin_config.get('options', {}).get('namespace')
            )
        else:
            self._custom_namespace_checkbox.setChecked(False)
            self._custom_namespace_line_edit.setEnabled(False)
        # set Signals
        self._button_group.buttonClicked.connect(self._on_radio_button_clicked)
        self._custom_namespace_checkbox.stateChanged.connect(
            self._on_checkbox_state_changed
        )
        self._custom_namespace_line_edit.textChanged.connect(
            self._on_namespace_changed
        )

    def _on_checkbox_state_changed(self, state):
        '''Enable or disable the custom namespace line edit based on checkbox state.'''
        self._custom_namespace_line_edit.setEnabled(state)
        self.set_plugin_option(
            'namespace', self._custom_namespace_line_edit.text()
        )
        if not state:
            self.set_plugin_option('namespace', None)

    def _on_namespace_changed(self, namespace):
        '''Update the namespace option based on the line edit text.'''
        if not namespace:
            return
        self.set_plugin_option('namespace', namespace)

    def _on_radio_button_clicked(self, radio_button):
        '''Toggle the custom namespace line edit based on checkbox state.'''
        self.set_plugin_option('load_type', radio_button.text().lower())
