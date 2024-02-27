# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.widgets import BaseWidget


class PhotoshopImageOptionsSelectorWidget(BaseWidget):
    '''Main class to represent image export options widget on a publish process.'''

    DEFAULT_SUPPORTED_FORMATS = [
        'jpg',
        'bmp',
        'eps',
        'gif',
        'pdf',
        'png',
        'tif',
    ]

    name = 'photoshop_image_options_selector'
    ui_type = 'qt'

    on_format_changed = QtCore.Signal(int)

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
        '''initialise PhotoshopImageExportOptionsWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''

        self._format_selector = None

        super(PhotoshopImageOptionsSelectorWidget, self).__init__(
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
        '''Build file export_type/format selector'''

        image_format_layout = QtWidgets.QHBoxLayout()

        image_format_layout.addWidget(QtWidgets.QLabel('Format:'))

        self._format_selector = QtWidgets.QComboBox()
        if 'compatible_types' in self.plugin_config.get('options', {}):
            # Filter out unsupported formats
            self._formats = [
                format_
                for format_ in self.DEFAULT_SUPPORTED_FORMATS
                if format_ in self.plugin_config['options']['compatible_types']
            ]
        else:
            self._formats = self.DEFAULT_SUPPORTED_FORMATS
        self._format_selector.addItems(self._formats)
        image_format_layout.addWidget(self._format_selector, 100)

        self.layout().addLayout(image_format_layout)

    def post_build_ui(self):
        '''hook events'''
        self._format_selector.currentIndexChanged.connect(
            self._on_format_changed
        )

        # Pre-select export_type
        export_type = self.plugin_config.get('options', {}).get('export_type')
        if export_type:
            self._format_selector.setCurrentIndex(
                self._formats.index(export_type)
            )

    def _on_format_changed(self, current_index):
        '''Callback when format is changed, with *current_índex* pointing
        the combobox index changed to.'''
        export_type = self._formats[current_index]
        self.set_plugin_option('export_type', export_type)
