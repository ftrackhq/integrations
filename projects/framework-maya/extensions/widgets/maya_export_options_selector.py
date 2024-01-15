# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget


class MayaExportOptionsSelectorWidget(BaseWidget):
    '''Main class to represent a scene widget on a publish process.'''

    name = 'maya_export_options_selector'
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
        self._construction_history_cb = None
        self._channels_cb = None
        self._preserve_references_cb = None
        self._shader_cb = None
        self._constraints_cb = None
        self._expressions_cb = None

        super(MayaExportOptionsSelectorWidget, self).__init__(
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
        self._construction_history_cb = QtWidgets.QCheckBox(
            'Construction History'
        )
        self._channels_cb = QtWidgets.QCheckBox('Channels')
        self._preserve_references_cb = QtWidgets.QCheckBox(
            'Preserve References'
        )
        self._shader_cb = QtWidgets.QCheckBox('Shader')
        self._constraints_cb = QtWidgets.QCheckBox('Constraints')
        self._expressions_cb = QtWidgets.QCheckBox('Expressions')

        self.layout().addWidget(self._construction_history_cb)
        self.layout().addWidget(self._channels_cb)
        self.layout().addWidget(self._preserve_references_cb)
        self.layout().addWidget(self._shader_cb)
        self.layout().addWidget(self._constraints_cb)
        self.layout().addWidget(self._expressions_cb)

    def post_build_ui(self):
        '''hook events'''
        self._construction_history_cb.stateChanged.connect(
            self._on_construction_history_changed
        )
        self._channels_cb.stateChanged.connect(self._on_channels_changed)
        self._preserve_references_cb.stateChanged.connect(
            self._on_preserve_references_changed
        )
        self._shader_cb.stateChanged.connect(self._on_shader_changed)
        self._constraints_cb.stateChanged.connect(self._on_constraints_changed)
        self._expressions_cb.stateChanged.connect(self._on_expressions_changed)

        provided_options = self.plugin_config.get('options')
        self._construction_history_cb.setChecked(
            provided_options.get('constructionHistory', False)
            if provided_options
            else False
        )
        self._channels_cb.setChecked(
            provided_options.get('channels', False)
            if provided_options
            else False
        )
        self._preserve_references_cb.setChecked(
            provided_options.get('preserveReferences', False)
            if provided_options
            else False
        )
        self._shader_cb.setChecked(
            provided_options.get('shader', False)
            if provided_options
            else False
        )
        self._constraints_cb.setChecked(
            provided_options.get('constraints', False)
            if provided_options
            else False
        )
        self._expressions_cb.setChecked(
            provided_options.get('expressions', False)
            if provided_options
            else False
        )

        # Manually call the signals on build
        self._on_construction_history_changed(None)
        self._on_channels_changed(None)
        self._on_preserve_references_changed(None)
        self._on_shader_changed(None)
        self._on_constraints_changed(None)
        self._on_expressions_changed(None)

    def _on_construction_history_changed(self, state):
        self.set_plugin_option(
            'constructionHistory', self._construction_history_cb.isChecked()
        )

    def _on_channels_changed(self, state):
        self.set_plugin_option('channels', self._channels_cb.isChecked())

    def _on_preserve_references_changed(self, state):
        self.set_plugin_option(
            'preserveReferences', self._preserve_references_cb.isChecked()
        )

    def _on_shader_changed(self, state):
        self.set_plugin_option('shader', self._shader_cb.isChecked())

    def _on_constraints_changed(self, state):
        self.set_plugin_option('constraints', self._constraints_cb.isChecked())

    def _on_expressions_changed(self, state):
        self.set_plugin_option('expressions', self._expressions_cb.isChecked())
