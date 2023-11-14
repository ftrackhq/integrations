# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

import ftrack_constants.framework as constants

from ftrack_framework_qt.widgets import BaseWidget

from ftrack_qt.widgets.icons import StatusMaterialIconWidget
from ftrack_utils.framework.tool_config.read import get_plugins


# TODO: review and docstring this code
class ValidatorCheckWidget(BaseWidget):
    '''Main class to represent a validator check widget on a publish process.'''

    name = 'validator_check'
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
        self._validator_status_icon = StatusMaterialIconWidget('check')
        self._validator_status_icon.setObjectName('borderless')
        self._validator_status_icon.set_status(constants.status.DEFAULT_STATUS)

        # Add the widgets to the layout
        self.layout().addWidget(self._validator_name_label)
        self.layout().addWidget(self._validator_status_icon)

    def post_build_ui(self):
        '''hook events'''
        pass

    def on_log_item_added_callback(self, plugin_info):
        if plugin_info['plugin_name'] == self.plugin_config['name']:
            if plugin_info['boolean_status']:
                self._validator_status_icon.set_status(
                    constants.status.SUCCESS_STATUS
                )
            else:
                self._validator_status_icon.set_status(
                    constants.status.ERROR_STATUS
                )
