# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets

from ftrack_framework_qt.widgets import BaseWidget
from ftrack_qt.widgets.selectors import OpenAssetSelector
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class ShowComponentWidget(BaseWidget):
    '''Main class to represent a component to be loaded'''

    name = "show_component"
    ui_type = "qt"

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
        '''Initialize PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._error_message_label = None
        self._asset_path_label = None
        self._asset_info_label = None
        self._component_path_label = None

        super(ShowComponentWidget, self).__init__(
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
        '''Set up the main layout for the widget.'''
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def build_ui(self):
        '''Build the user interface for the widget.'''

        self._error_message_label = QtWidgets.QLabel()
        self._error_message_label.setStyleSheet(
            "font-style: italic; font-weight: bold; color: red;"
        )
        self._error_message_label.setVisible(False)

        asset_widget = QtWidgets.QWidget()
        asset_widget.setLayout(QtWidgets.QHBoxLayout())

        label = QtWidgets.QLabel('Asset to load:')
        label.setProperty('secondary', True)
        asset_widget.layout().addWidget(label)

        self._asset_info_label = QtWidgets.QLabel()
        self._asset_info_label.setProperty('h2', True)
        asset_widget.layout().addWidget(self._asset_info_label, 100)

        path_widget = QtWidgets.QWidget()
        path_widget.setLayout(QtWidgets.QHBoxLayout())

        label = QtWidgets.QLabel('Path:')
        label.setProperty('secondary', True)
        path_widget.layout().addWidget(label)

        self._component_path_label = QtWidgets.QLabel()
        self._component_path_label.setProperty('h2', True)
        path_widget.layout().addWidget(self._component_path_label, 100)

        self.layout().addWidget(asset_widget)
        self.layout().addWidget(path_widget)

    def post_build_ui(self):
        '''Perform post-construction operations.'''
        pass

    def populate(self):
        '''Fetch info from plugin to populate the widget'''
        self._resolve_component()

    def _resolve_component(self):
        '''Query assets based on the context and asset type.'''
        payload = self.plugin_config['options']
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Handle the result of the UI hook.'''
        super(ShowComponentWidget, self).ui_hook_callback(ui_hook_result)
        if 'error_message' in ui_hook_result:
            self._error_message_label.setText(ui_hook_result['error_message'])
            self._error_message_label.setVisible(True)
            return
        self._asset_info_label.setText(ui_hook_result['context_path'])
        self._component_path_label.setText(ui_hook_result['component_path'])
