# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline_qt.client.widgets.client_ui import BaseUIWidget
from ftrack_connect_pipeline_qt import constants

from Qt import QtWidgets, QtCore, QtGui


class ComponentButton(QtWidgets.QPushButton):
    status_icons = constants.icons.status_icons

    def __init__(self, component_name, status, parent=None):
        super(ComponentButton, self).__init__(parent)

        self.component_name = component_name
        self.status = status

        self.build()
        self.post_build()

    def build(self):
        self.setMinimumHeight(100)  # Set minimum otherwise it will collapse the container
        self.setMinimumWidth(200)
        # self.setCheckable(True)
        # self.setAutoExclusive(True)
        self.setContentsMargins(20, 20, 20, 20)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.icon_widget = QtWidgets.QLabel()
        self.layout().addWidget(self.icon_widget)
        self.set_icon_status(constants.DEFAULT_STATUS)

        v_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(v_layout)

        text_widget = QtWidgets.QLabel(self.component_name)
        v_layout.addWidget(text_widget)
        self.status_message_widget = QtWidgets.QLabel(self.status)
        v_layout.addWidget(self.status_message_widget)

        self.error_widget = QtWidgets.QLabel()
        self.layout().addWidget(self.error_widget)
        icon = self.status_icons[constants.ERROR_STATUS]
        self.error_widget.setPixmap(icon)
        self.error_widget.hide()

    def post_build(self):
        self.clicked.connect(self.show_log)

    def update_status(self, status, status_message, results):
        self.status_message_widget.setText(status_message)
        self.set_icon_status(status)
        if status == constants.ERROR_STATUS:
            self.update_error_message(results)

    def set_icon_status(self, status):
        icon = self.status_icons[status]
        self.icon_widget.setPixmap(icon)
        # if message:
        #     self.setToolTip(str(message))

    def update_error_message(self, results):
        self.error_widget.show()
        message = None
        logged_errors = []
        if results:
            for stage_result in results:
                if stage_result.get('status') == False:
                    for plugin_result in stage_result.get('result'):
                        plug_error = 'Plugin {} failed with message: {}'.format(
                            plugin_result.get('name'),
                            plugin_result.get('message')
                        )
                        logged_errors.append(plug_error)
        if logged_errors:
            message = "\n".join(logged_errors)

        self.error_widget.setToolTip(str(message))

    def show_log(self):
        # TODO: we can show the status and the error message here
        pass


class MainButtonWidget(QtWidgets.QPushButton):
    status_icons = constants.icons.status_icons

    def __init__(self, parent=None):
        super(MainButtonWidget, self).__init__(parent)

        self.status = constants.DEFAULT_STATUS

        self.build()

    def build(self):

        self.setStyleSheet("""
            QPushButton {
                background-color: grey;
                border: none;
            }
            """)
        self.setMinimumHeight(50)
        self.setMinimumWidth(300)
        # self.setFlat(True)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.status_label = QtWidgets.QLabel(self.status)
        show_more = QtWidgets.QLabel("SHOW MORE")
        self.layout().addWidget(self.status_label)
        self.layout().addStretch()
        self.layout().addWidget(show_more)

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status
        self.status_label.setText(status)


class ProgressWidget(BaseUIWidget):
    '''Widget representation of a boolean'''
    component_widgets = {}

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        self.content_widget = None

        super(ProgressWidget, self).__init__(
            name, fragment_data, parent=parent
        )
        self.step_types = []

    def build(self):
        self._widget = MainButtonWidget()
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)
        # self.widget.setSizePolicy(
        #     QtWidgets.QSizePolicy.Preferred,
        #     QtWidgets.QSizePolicy.Fixed
        # )
        # self.widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.content_widget = QtWidgets.QWidget()
        inner_widget = QtWidgets.QVBoxLayout()
        self.content_widget.setLayout(inner_widget)
        self.content_widget.hide()

    def post_build(self):
        '''post build function , mostly used connect widgets events.'''
        self._widget.clicked.connect(self._show_widget)

    def _show_widget(self):
        self.content_widget.show()

    def add_component(self, step_type, step_name):
        id_name = "{}.{}".format(step_type, step_name)
        component_name = step_name
        component_button = ComponentButton(component_name, "Not started")
        self.component_widgets[id_name] = component_button
        if step_type not in self.step_types:
            self.step_types.append(step_type)
            step_title = QtWidgets.QLabel(step_type)
            self.content_widget.layout().addWidget(step_title)
        self.content_widget.layout().addWidget(component_button)

    def update_component_status(
            self, step_type, step_name, status, status_message, results
    ):
        id_name = "{}.{}".format(step_type, step_name)
        self.component_widgets[id_name].update_status(
            status, status_message, results
        )
        if status != self.widget.get_status():
            self.widget.set_status(status)


