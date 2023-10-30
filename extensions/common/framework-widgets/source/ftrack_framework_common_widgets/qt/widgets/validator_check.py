# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

import ftrack_constants.framework as constants

from ftrack_framework_qt.widgets import BaseWidget

from ftrack_qt.widgets.icons import StatusMaterialIconWidget


# TODO: review and docstring this code
class ValidatorCheckWidget(BaseWidget):
    '''Main class to represent a context widget on a publish process.'''

    name = 'validator_check'
    ui_type = 'qt'

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        dialog_connect_methods_callback,
        dialog_property_getter_connection_callback,
        parent=None,
    ):
        '''initialise PublishContextWidget with *parent*, *session*, *data*,
        *name*, *description*, *options* and *context*
        '''
        self._validator_name_label = None
        self._validator_status_icon = None
        self._check_button = None

        super(ValidatorCheckWidget, self).__init__(
            event_manager,
            client_id,
            context_id,
            plugin_config,
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
        self._validator_status_icon = StatusMaterialIconWidget('check')
        self._validator_status_icon.setObjectName('borderless')
        self._check_button = QtWidgets.QPushButton('check_validator')
        self._validator_status_icon.set_status(constants.status.DEFAULT_STATUS)

        # Add the widgets to the layout
        self.layout().addWidget(self._validator_name_label)
        self.layout().addWidget(self._validator_status_icon)
        self.layout().addWidget(self._check_button)

    def post_build_ui(self):
        '''hook events'''
        self._check_button.clicked.connect(self._on_check_clicked)

    def _on_check_clicked(self):
        '''Updates the options dictionary with provided *status* when
        currentIndexChanged of status_selector event is triggered'''
        # This is async, so once the result arrive to the run_plugin_callback,
        # we set the status
        arguments = {"plugin_widget_id": self.id}
        self.dialog_method_connection('run_collectors', arguments=arguments)
        self._validator_status_icon.set_status(constants.status.RUNNING_STATUS)

    def run_plugin_callback(self, plugin_info):
        # In case we have run the collectors
        if plugin_info['plugin_type'] == 'collector':
            self.validate_collector_result(plugin_info['plugin_method_result'])
        # We have run the validate method
        if (
            plugin_info['plugin_widget_id'] == self.id
            and plugin_info['plugin_method'] == 'validate'
        ):
            if plugin_info['plugin_method_result']:
                self._validator_status_icon.set_status(
                    constants.status.SUCCESS_STATUS
                )
            else:
                self._validator_status_icon.set_status(
                    constants.status.ERROR_STATUS
                )

    def validate_collector_result(self, collector_result):
        self.plugin_data = {'collector_result': collector_result}
        print(collector_result)
        self.run_plugin_method('validate')
