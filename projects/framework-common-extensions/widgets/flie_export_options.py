# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.widgets import BaseWidget


class FileExportOptionsWidget(BaseWidget):
    '''Main class to represent a file publish export options widget on a publish process.'''

    name = 'file_exporter_options'
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
        '''initialise FileExportOptionsWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''

        super(FileExportOptionsWidget, self).__init__(
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
            if type(value) == str:
                value_widget = QtWidgets.QLineEdit(value)
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

            h_layout.addWidget(option_widget)
            h_layout.addWidget(value_widget)
            self.layout().addLayout(h_layout)

    def post_build_ui(self):
        '''hook events'''
        pass

    def _on_option_changed(self, option, value):
        self.set_plugin_option(option, value)
