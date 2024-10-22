# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


from PySide6 import QtWidgets, QtCore


from ftrack_framework_qt.widgets import BaseWidget


class BlenderSceneOptionsSelectorWidget(BaseWidget):
    '''Widget to choose between export type and export format'''

    name = 'blender_scene_options_selector'
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
        self._export_type_cb = None
        self._extension_format_cb = None

        super(BlenderSceneOptionsSelectorWidget, self).__init__(
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
        # Create export type combo box
        self._export_type_cb = QtWidgets.QComboBox()
        self._export_type_cb.addItems(["scene", "selection"])
        self.layout().addWidget(self._export_type_cb)

        # Create extension format type combo box
        self._extension_format_cb = QtWidgets.QComboBox()
        self._extension_format_cb.addItems(["mb", "ma"])
        self.layout().addWidget(self._extension_format_cb)

    def post_build_ui(self):
        '''hook events'''
        self._export_type_cb.currentTextChanged.connect(
            self._on_export_changed
        )
        default_export_type = self.plugin_config['options'].get(
            'export_type', 'scene'
        )
        self._export_type_cb.setCurrentText(default_export_type)

        self._extension_format_cb.currentTextChanged.connect(
            self._on_export_changed
        )
        default_extension_format = self.plugin_config['options'].get(
            'extension_format', 'mb'
        )
        self._extension_format_cb.setCurrentText(default_extension_format)

        # Manually call the signals on build
        self._on_export_changed(default_export_type)
        self._on_extension_changed(default_extension_format)

    def _on_export_changed(self, export_type):
        '''Updates the option dictionary with provided *export_type* when
        the selected export type in the combobox has changed'''
        if not export_type:
            return
        self.set_plugin_option('export_type', export_type)

    def _on_extension_changed(self, extension_format):
        '''Updates the option dictionary with provided *extension_format* when
        the selected extension format in the combobox has changed'''
        if not extension_format:
            return
        self.set_plugin_option('extension_format', extension_format)
