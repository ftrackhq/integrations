# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class AfterEffectsOutputTemplatesSelectorWidget(BaseWidget):
    '''Drop-down list to select the desired template for movie render.'''

    name = 'aftereffects_output_templates_selector'
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
        self._template_cb = None

        super(AfterEffectsOutputTemplatesSelectorWidget, self).__init__(
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
        self._template_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self._template_cb)

    def post_build_ui(self):
        '''hook events'''
        self._template_cb.currentTextChanged.connect(self._on_template_changed)

    def populate(self):
        '''Fetch info from plugin to populate the widget'''
        self.query_templates()

    def query_templates(self):
        '''Query All templates from local After Effects installation.'''
        payload = {}
        self.run_ui_hook(payload)

    @invoke_in_qt_main_thread
    def ui_hook_callback(self, ui_hook_result):
        '''Handle the result of the UI hook.'''
        super(
            AfterEffectsOutputTemplatesSelectorWidget, self
        ).ui_hook_callback(ui_hook_result)
        self._template_cb.addItems(ui_hook_result)
        default_template_name = self.plugin_config['options'].get(
            'template_name', 'H.264 - Match Render Settings - 15 Mbps'
        )
        self._template_cb.setCurrentText(default_template_name)

    def _on_template_changed(self, template_name):
        '''Updates the template_name option with the provided *template_name'''
        if not template_name:
            return
        self.set_plugin_option('template_name', template_name)
