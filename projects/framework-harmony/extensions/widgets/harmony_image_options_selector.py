# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget


class HarmonyImageOptionsSelectorWidget(BaseWidget):
    '''Main class to represent image export options widget on a publish process.'''

    DEFAULT_SUPPORTED_FORMATS = {
        'bmp': ['bmp4'],
        'dpx': [
            'dpx3_8',
            'dpx3_10',
            'dpx3_12',
            'dpx3_16',
            'dpx3_10_inverted_channels',
            'dpx3_12_inverted_channels',
            'dpx3_16_inverted_channels',
        ],
        'dtex': [],
        'exr': [],
        'jpg': [],
        'opt': ['opt1', 'opt3', 'opt4'],
        'pal': [],
        'pdf': [],
        'png': ['png4', 'pngdp', 'pngdp3', 'pngdp4'],
        'psd': ['psd1', 'psd1', 'psd1'],
        'psddp': ['psddp1', 'psddp3', 'psddp4'],
        'scan': [],
        'sgi': ['sgi1', 'sgi3', 'sgi4', 'sgidp', 'sgidp3', 'sgidp4'],
        'tga': ['tga1', 'tga3', 'tga4'],
        'tif': [],
        'tvg': [],
        'var': [],
        'yuv': [],
    }

    name = 'harmony_image_options_selector'
    ui_type = 'qt'

    @property
    def formats(self):
        return list(self.DEFAULT_SUPPORTED_FORMATS.keys())

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
        '''initialise HarmonyImageExportOptionsWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''

        self._format_selector = None
        self._format_option_selector = None

        super(HarmonyImageOptionsSelectorWidget, self).__init__(
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
        self._format_selector.addItems(self.formats)
        image_format_layout.addWidget(self._format_selector, 100)

        self.layout().addLayout(image_format_layout)

        image_format_option_layout = QtWidgets.QHBoxLayout()

        image_format_option_layout.addWidget(
            QtWidgets.QLabel('Format option:')
        )

        self._format_option_selector = QtWidgets.QComboBox()
        image_format_option_layout.addWidget(self._format_option_selector, 100)

        self.layout().addLayout(image_format_option_layout)

    def post_build_ui(self):
        '''hook events'''
        self._format_selector.currentIndexChanged.connect(
            self._on_format_changed
        )
        self._format_option_selector.currentIndexChanged.connect(
            self._on_format_option_changed
        )

        # Pre-select export_type and options
        export_type = self.plugin_config.get('options', {}).get('export_type')
        export_format = self.plugin_config.get('options', {}).get(
            'export_format'
        )
        if export_type:
            self._format_selector.setCurrentIndex(
                self.formats.index(export_type)
            )
            if export_format and len(export_format) > 0:
                format_options = self.DEFAULT_SUPPORTED_FORMATS[export_type]
                self._format_option_selector.setCurrentIndex(
                    format_options.index(export_type) + 1
                )

    def _on_format_changed(self, current_index):
        '''Callback when format is changed, with *current_índex* pointing
        the combobox index changed to.'''
        self.logger.debug(f'Format changed to {current_index}')
        export_type = self.formats[current_index]
        self.set_plugin_option('export_type', export_type)
        # Deploy options
        self._format_option_selector.clear()
        format_options = self.DEFAULT_SUPPORTED_FORMATS[export_type]
        self._format_option_selector.addItems([''] + format_options)

    def _on_format_option_changed(self, current_index):
        '''Callback when format option is changed, with *current_índex* pointing
        the combobox index changed to.'''
        self.logger.debug(f'Format option changed to {current_index}')
        if current_index > 0:
            export_type = self.formats[self._format_selector.currentIndex()]
            format_option = self.DEFAULT_SUPPORTED_FORMATS[export_type][
                current_index - 1
            ]
            self.set_plugin_option('export_format', format_option)
        else:
            self.set_plugin_option('export_format', '')
