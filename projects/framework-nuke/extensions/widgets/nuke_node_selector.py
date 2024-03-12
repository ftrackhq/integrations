# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class NukeWritenodeSelectorWidget(BaseWidget):
    '''Drop-down list to select the desired writenode.'''

    name = 'nuke_node_selector'
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
        self._writenode_cb = None

        super(NukeWritenodeSelectorWidget, self).__init__(
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
        self._writenode_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self._writenode_cb)

    def post_build_ui(self):
        '''hook events'''
        self._writenode_cb.currentTextChanged.connect(
            self._on_writenode_changed
        )

    def populate(self):
        '''Fetch info from plugin to populate the widget'''
        self.query_writenodes()

    def query_writenodes(self):
        '''Query All write nodes from script.'''
        payload = {}
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Handle the result of the UI hook.'''
        super(NukeWritenodeSelectorWidget, self).ui_hook_callback(
            ui_hook_result
        )
        self._writenode_cb.addItems(ui_hook_result)
        default_node_name = self.plugin_config['options'].get(
            'node_name', 'Write1'
        )
        self._writenode_cb.setCurrentText(default_node_name)

    def _on_writenode_changed(self, node_name):
        '''Updates the node_name option with the provided *node_name'''
        if not node_name:
            return
        self.set_plugin_option('node_name', node_name)
