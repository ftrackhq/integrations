# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.ui.utility.widget import overlay
from ftrack_connect_pipeline_qt import utils
from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import (
    MaterialIconWidget,
)
from ftrack_connect_pipeline_qt.utils import set_property
from ftrack_connect_pipeline_qt.utils import str_version


class PhaseButton(QtWidgets.QPushButton):
    '''Showing progress of a phase(component)'''

    status_icons = constants.icons.status_icons

    def __init__(self, phase_name, status, parent=None):
        super(PhaseButton, self).__init__(parent)

        self.phase_name = phase_name
        self.status = status

        self.logged_errors = []

        self.build()
        self.post_build()

    def build(self):
        self.setMinimumHeight(
            32
        )  # Set minimum otherwise it will collapse the container
        self.setMinimumWidth(200)
        # self.setCheckable(True)
        # self.setAutoExclusive(True)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(3, 3, 3, 3)

        self.icon_widget = MaterialIconWidget(None)
        self.layout().addWidget(self.icon_widget)
        self.set_status(constants.DEFAULT_STATUS)

        v_layout = QtWidgets.QVBoxLayout()

        phase_name_widget = QtWidgets.QLabel(self.phase_name)
        phase_name_widget.setObjectName('h3')
        v_layout.addWidget(phase_name_widget)
        self.status_message_widget = QtWidgets.QLabel(self.status)
        self.status_message_widget.setObjectName('gray')
        v_layout.addWidget(self.status_message_widget)

        self.layout().addLayout(v_layout, 100)

        self.log_widget = QtWidgets.QWidget()
        self.log_widget.setLayout(QtWidgets.QVBoxLayout())
        self.log_widget.layout().addSpacing(30)

        self.log_text_edit = QtWidgets.QTextEdit()
        self.log_widget.layout().addWidget(self.log_text_edit)
        self.overlay_container = overlay.Overlay(self.log_widget)
        self.overlay_container.setVisible(False)

    def post_build(self):
        self.clicked.connect(self.show_log)

    def update_status(self, status, status_message, results):
        self.status_message_widget.setText(status_message)
        self.set_status(status)
        if status == constants.ERROR_STATUS:
            self.update_error_message(results)

    def set_status(self, status):
        self.icon_widget.set_status(status)

    def update_error_message(self, results):
        message = None
        self.logged_errors = []
        if results:
            for stage_result in results:
                if stage_result.get('status') == False:
                    for plugin_result in stage_result.get('result'):
                        plug_error = (
                            'Plugin {} failed with message: {}'.format(
                                plugin_result.get('name'),
                                plugin_result.get('message'),
                            )
                        )
                        self.logged_errors.append(plug_error)
        if self.logged_errors:
            message = "\n".join(self.logged_errors)

        self.setToolTip(str(message))

    def show_log(self):
        self.overlay_container.setParent(self.parent())
        if self.logged_errors:
            message = "\n".join(self.logged_errors)
            self.log_text_edit.setText(message)
        else:
            self.log_text_edit.setText("No errors found")
        self.overlay_container.setVisible(True)
        self.overlay_container.resize(self.parent().size())


class StatusButtonWidget(QtWidgets.QPushButton):
    status_icons = constants.icons.status_icons

    VIEW_COLLAPSED_BUTTON = 'collapsed-button'  # AM (Opens progress overlay)
    VIEW_EXPANDED_BUTTON = 'expanded-button'  # Opener/Assembler/Publisher (Opens progress overlay)
    VIEW_EXPANDED_BANNER = 'expanded-banner'  # Progress overlay

    def __init__(self, view_mode, parent=None):
        super(StatusButtonWidget, self).__init__(parent)

        self.status = None
        self._view_mode = view_mode or self.VIEW_EXPANDED_BUTTON

        self.build()

    def build(self):

        self.setObjectName('status-widget-{}'.format(self._view_mode))

        self.setMinimumHeight(32)

        if self._view_mode == self.VIEW_COLLAPSED_BUTTON:
            self.setMaximumHeight(32)
            self.setMinimumWidth(32)
            self.setMaximumWidth(32)
        else:
            self.setMinimumWidth(300)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(6, 6, 6, 6)
        self.layout().setSpacing(1)
        self.message_label = QtWidgets.QLabel()
        self.layout().addWidget(self.message_label)
        self.layout().addStretch()
        self.status_icon = MaterialIconWidget(None)
        self.layout().addWidget(self.status_icon)

        self.set_status(constants.SUCCESS_STATUS)

    def get_status(self):
        return self.status

    def set_status(self, status, message=''):
        self.status = status or constants.DEFAULT_STATUS
        self.message = message
        self.message_label.setText(self.message)
        set_property(self, 'status', self.status.lower())
        color = self.status_icon.set_status(self.status, size=24)
        self.message_label.setStyleSheet('color: #{}'.format(color))
        # for widget in [self, self.message_label]:
        #    widget.style().unpolish(widget)
        #    widget.style().polish(widget)
        #    widget.update()


class ProgressWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    component_widgets = {}

    def __init__(
        self, name, fragment_data, parent=None, status_view_mode=None
    ):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        self.content_widget = None
        self.status_banner = None
        self._status_view_mode = status_view_mode

        super(ProgressWidget, self).__init__(
            name, fragment_data, parent=parent
        )
        self.step_types = []

    def build(self):
        self._widget = StatusButtonWidget(self._status_view_mode)
        self.set_status_widget_visibility(False)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.content_widget = QtWidgets.QFrame()
        self.content_widget.setObjectName('overlay')
        self.content_widget.setLayout(QtWidgets.QVBoxLayout())
        self.content_widget.layout().setContentsMargins(15, 15, 15, 15)

        self.scroll.setWidget(self.content_widget)

        self.overlay_container = overlay.Overlay(self.scroll)
        self.overlay_container.setVisible(False)

    def post_build(self):
        '''post build function , mostly used connect widgets events.'''
        self.widget.clicked.connect(self.show_widget)

    def show_widget(self):
        main_window = utils.get_main_framework_window_from_widget(self.widget)
        if main_window:
            self.overlay_container.setParent(main_window)
        self.overlay_container.setVisible(True)
        self.widget.setVisible(True)

    def hide_widget(self):
        self.widget.setVisible(False)

    def prepare_add_components(self):
        self.clear_components()
        self.status_banner = StatusButtonWidget(
            StatusButtonWidget.VIEW_EXPANDED_BANNER
        )
        self.content_widget.layout().addWidget(self.status_banner)

    def add_component(self, step_type, step_name, version_id=None):
        id_name = "{}.{}.{}".format(version_id or '-', step_type, step_name)
        component_name = step_name
        component_button = PhaseButton(component_name, "Not started")
        self.component_widgets[id_name] = component_button
        if step_type not in self.step_types:
            self.step_types.append(step_type)
            step_title = QtWidgets.QLabel(step_type.title())
            self.content_widget.layout().addWidget(step_title)
        self.content_widget.layout().addWidget(component_button)

    def components_added(self):
        self.content_widget.layout().addStretch()

    def clear_components(self):
        for i in reversed(range(self.content_widget.layout().count())):
            if self.content_widget.layout().itemAt(i).widget():
                self.content_widget.layout().itemAt(i).widget().deleteLater()
        self.step_types = []

    def set_status(self, status, message=None):
        self.widget.set_status(status, message=message)
        if self.status_banner:
            self.status_banner.set_status(status, message=message)
        self.set_status_widget_visibility(True)

    def set_status_widget_visibility(self, visibility=False):
        self.widget.setVisible(visibility)

    def update_component_status(
        self, step_type, step_name, status, status_message, results, version_id
    ):
        id_name = "{}.{}.{}".format(version_id or '-', step_type, step_name)
        if id_name in self.component_widgets:
            self.component_widgets[id_name].update_status(
                status, status_message, results
            )
            if status != self.widget.get_status():
                main_status_message = '{}: {}'.format(id_name, status_message)
                self.widget.set_status(status, message=main_status_message)
                if self.status_banner:
                    self.status_banner.set_status(
                        status, message=main_status_message
                    )


class BatchProgressWidget(ProgressWidget):
    def __init__(
        self, name, fragment_data, parent=None, status_view_mode=None
    ):
        super(BatchProgressWidget, self).__init__(
            name,
            fragment_data,
            parent=parent,
            status_view_mode=status_view_mode,
        )

    def add_version(self, component):
        version_widget = QtWidgets.QLabel(
            '{} | {}'.format(
                str_version(component['version']).replace('/', ' | '),
                component['name'],
            )
        )
        version_widget.setObjectName('h2')
        self.content_widget.layout().addWidget(version_widget)
