# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.widgets import BaseWidget


class ValidatorLabelWidget(BaseWidget):
    '''Main class to represent a validator widget on a publish process.'''

    name = 'validator_label'
    ui_type = 'qt'

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        group_config,
        dialog_connect_methods_callback,
        dialog_property_getter_connection_callback,
        parent=None,
    ):
        self._validator_name_label = None

        super(ValidatorLabelWidget, self).__init__(
            event_manager,
            client_id,
            context_id,
            plugin_config,
            group_config,
            dialog_connect_methods_callback,
            dialog_property_getter_connection_callback,
            parent,
        )

    def pre_build_ui(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build_ui(self):
        '''build function widgets.'''
        self._validator_name_label = QtWidgets.QLabel(self.plugin_name)

        # Add the widgets to the layout
        self.layout().addWidget(self._validator_name_label)

    def post_build_ui(self):
        '''hook events'''
        pass
