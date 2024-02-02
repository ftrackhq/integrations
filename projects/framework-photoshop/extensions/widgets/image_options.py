# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.widgets import BaseWidget


class ImageExportOptionsWidget(BaseWidget):
    '''Main class to represent image export options widget on a publish process.'''

    name = 'image_options'
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
        '''initialise FileExportOptionsWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''

        self._format_selector = None

        super(ImageExportOptionsWidget, self).__init__(
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
        '''Build file extension/format selector'''

        image_format_layout = QtWidgets.QHBoxLayout()

        image_format_layout.addWidget(QtWidgets.QLabel('Image format:'))

        self._extensions = self.plugin_config.get('options').get(
            'extensions'
        ) or [".jpg"]

        self._format_selector = QtWidgets.QComboBox()
        self._format_selector.addItems(self._extensions)
        image_format_layout.addWidget(self._format_selector, 100)

        self.layout().addLayout(image_format_layout)

    def post_build_ui(self):
        '''hook events'''
        self._format_selector.currentIndexChanged.connect(
            self._on_format_changed
        )

        # Pre-select extension
        extension = self.plugin_config.get('options').get('extension')
        if extension:
            self._format_selector.setCurrentIndex(
                self._extensions.index(extension)
            )

    def _on_format_changed(self, currentIndex):
        '''Callback when format is changed'''
        extension = self._extensions[currentIndex]
        self.set_plugin_option('extension', extension)
