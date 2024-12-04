# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget


class PhotoshopDocumentOptionsSelectorWidget(BaseWidget):
    '''Main class to represent a document widget on a publish process.'''

    name = 'photoshop_document_options_selector'
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
        self._extension_format_cb = None

        super(PhotoshopDocumentOptionsSelectorWidget, self).__init__(
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

        # Create extension format type combo box
        self._extension_format_cb = QtWidgets.QComboBox()
        self._extension_format_cb.addItems(["psd", "psb"])
        self.layout().addWidget(self._extension_format_cb)

    def post_build_ui(self):
        '''hook events'''

        default_extension_format = self.plugin_config['options'].get(
            'extension_format', 'psd'
        )
        self._extension_format_cb.setCurrentText(default_extension_format)

        self._extension_format_cb.currentTextChanged.connect(
            self._on_extension_format_changed
        )

        # Manually call the signals on build
        self._on_extension_format_changed(default_extension_format)

    def _on_extension_format_changed(self, extension_format):
        '''Updates the option dictionary with provided *extension_format* when
        the selected extension format in the combobox has changed'''
        if not extension_format:
            return
        self.set_plugin_option('extension_format', extension_format)
