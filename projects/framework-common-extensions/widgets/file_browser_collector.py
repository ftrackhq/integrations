# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os.path

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.widgets import BaseWidget

from ftrack_qt.widgets.browsers import FileBrowser


class FileBrowserWidget(BaseWidget):
    '''Main class to represent a context widget on a publish process.'''

    name = 'file_browser_collector'
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
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._file_browser = None

        super(FileBrowserWidget, self).__init__(
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
        # Create file browser
        self._file_browser = FileBrowser()
        self.layout().addWidget(self._file_browser)

    def post_build_ui(self):
        '''hook events'''
        self._file_browser.path_changed.connect(self._on_path_changed)

    def _on_path_changed(self, file_path):
        '''Updates the option dictionary with provided *asset_name* when
        asset_changed of asset_selector event is triggered'''
        if not file_path:
            return
        self.set_plugin_option('folder_path', os.path.dirname(file_path))
        self.set_plugin_option('file_name', os.path.basename(file_path))
