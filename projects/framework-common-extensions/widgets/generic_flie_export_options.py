# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_framework_qt.widgets import BaseWidget


class GenericFileExportOptionsWidget(BaseWidget):
    '''Main class to represent a file publish export options widget on a publish process.'''

    name = 'generic_file_exporter_options'
    ui_type = 'qt'

    rename_component = QtCore.Signal(object)

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

        super(GenericFileExportOptionsWidget, self).__init__(
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
        # Create options:
        for option, value in self.plugin_config.get('options').items():
            h_layout = QtWidgets.QHBoxLayout()
            option_widget = QtWidgets.QLabel(option)
            value_widget = None
            editable = True
            if option == 'rename':
                if value == 'auto':
                    editable = False
                elif value == True:
                    editable = True
                    value = ''
                else:
                    editable = False

            if type(value) == str:
                value_widget = QtWidgets.QLineEdit(value)
                value_widget.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
                value_widget.setReadOnly(not editable)
                value_widget.setEnabled(editable)
                value_widget.textChanged.connect(
                    partial(self._on_option_changed, option)
                )
            elif type(value) == bool:
                # TODO: implement
                pass
            elif type(value) == list:
                # TODO: implement
                pass
            elif type(value) == dict:
                # TODO: implement
                pass
            else:
                value_widget = QtWidgets.QLineEdit(value)
                value_widget.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

            h_layout.addWidget(option_widget)
            h_layout.addWidget(value_widget)
            self.layout().addLayout(h_layout)

    def post_build_ui(self):
        '''hook events'''
        pass

    def _on_option_changed(self, option, value):
        self.set_plugin_option(option, value)
        if option == 'rename':
            self.rename_component.emit(value)
