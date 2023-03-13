# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import shiboken2

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.utils import str_version

import ftrack_connect_pipeline_qt.ui.utility.widget.button
from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject
from ftrack_connect_pipeline_qt.ui.utility.widget import overlay, scroll_area
from ftrack_connect_pipeline_qt import utils
from ftrack_connect_pipeline_qt.ui.utility.widget.icon import (
    MaterialIconWidget,
)
from ftrack_connect_pipeline_qt.utils import set_property


class PhaseButton(QtWidgets.QPushButton):
    '''Showing progress of a phase(component)'''

    def __init__(self, phase_name, status, parent=None):
        super(PhaseButton, self).__init__(parent=parent)

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

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(3, 3, 3, 3)

        self.icon_widget = MaterialIconWidget(None)
        self.layout().addWidget(self.icon_widget)
        self.set_status(core_constants.DEFAULT_STATUS)

        v_layout = QtWidgets.QVBoxLayout()

        phase_name_widget = QtWidgets.QLabel(self.phase_name)
        phase_name_widget.setObjectName('h3')
        v_layout.addWidget(phase_name_widget)
        self.status_message_widget = QtWidgets.QLabel(self.status)
        self.status_message_widget.setObjectName('gray')
        v_layout.addWidget(self.status_message_widget)

        self.layout().addLayout(v_layout, 100)

        self.log_widget = QtWidgets.QFrame()
        self.log_widget.setVisible(False)
        self.log_widget.setLayout(QtWidgets.QVBoxLayout())
        self.log_widget.layout().addSpacing(10)

        self.log_text_edit = QtWidgets.QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_widget.layout().addWidget(self.log_text_edit, 10)
        self._close_button = (
            ftrack_connect_pipeline_qt.ui.utility.widget.button.ApproveButton(
                'HIDE LOG'
            )
        )
        self.log_widget.layout().addWidget(self._close_button)
        self.overlay_container = overlay.Overlay(self.log_widget)
        self.overlay_container.setVisible(False)

    def post_build(self):
        self.clicked.connect(self.show_log)
        self._close_button.clicked.connect(self.overlay_container.close)

    def update_status(self, status, status_message, results):
        # Make sure widget not has been destroyed
        if shiboken2.isValid(self.status_message_widget):
            self.status_message_widget.setText(status_message)
        self.set_status(status)
        if status == core_constants.ERROR_STATUS:
            self.update_error_message(results)

    def set_status(self, status):
        self.icon_widget.set_status(status)

    def update_error_message(self, results):
        message = None
        self.logged_errors = []
        if results:
            if isinstance(results, dict):
                for stage_result in results:
                    if stage_result.get('status') is False:
                        for plugin_result in stage_result.get('result'):
                            plug_error = (
                                'Plugin {} failed with message: {}'.format(
                                    plugin_result.get('name'),
                                    plugin_result.get('message'),
                                )
                            )
                            self.logged_errors.append(plug_error)
            else:
                self.logged_errors.append(
                    'Operation failed with error: {}'.format(str(results))
                )
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
        self.log_widget.setVisible(True)
        self.overlay_container.resize(self.parent().size())


class StatusButtonWidget(QtWidgets.QPushButton):
    '''Progress status button representation'''

    VIEW_COLLAPSED_BUTTON = 'collapsed-button'  # AM (Opens progress overlay)
    VIEW_EXPANDED_BUTTON = 'expanded-button'  # Opener/Assembler/Publisher (Opens progress overlay)
    VIEW_EXPANDED_BANNER = 'expanded-banner'  # Progress overlay

    def __init__(self, view_mode, parent=None):
        super(StatusButtonWidget, self).__init__(parent=parent)

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
            self.setMinimumWidth(200)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(6, 6, 6, 6)
        self.layout().setSpacing(1)
        self._message_label = QtWidgets.QLabel()
        self.layout().addWidget(self._message_label)
        self.layout().addStretch()
        self._status_icon = MaterialIconWidget(None)
        self.layout().addWidget(self._status_icon)

        self.set_status(core_constants.SUCCESS_STATUS)

    def get_status(self):
        return self.status

    def set_status(self, status, message=''):
        self.status = status or core_constants.DEFAULT_STATUS
        self.message = message
        self._message_label.setText(self.message)
        set_property(self, 'status', self.status.lower())
        color = self._status_icon.set_status(self.status, size=24)
        self._message_label.setStyleSheet('color: #{}'.format(color))


class ProgressWidgetObject(BaseUIWidgetObject):
    '''Widget representation of the progress widget used during schema run'''

    MARGINS = 15

    _step_widgets = {}

    def __init__(
        self, name, fragment_data, parent=None, status_view_mode=None
    ):
        '''Initialise ProgressWidgetObject with *name*,
        *fragment_data*, and *parent*'''

        self.content_widget = None
        self.status_banner = None
        self._status_view_mode = status_view_mode
        super(ProgressWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )
        self.step_types = []

    def build(self):
        self._widget = StatusButtonWidget(self._status_view_mode)
        self.set_status_widget_visibility(False)

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)

        self.content_widget = QtWidgets.QFrame()
        self.content_widget.setObjectName('overlay')
        self.content_widget.setLayout(QtWidgets.QVBoxLayout())
        self.content_widget.layout().setContentsMargins(
            self.MARGINS, self.MARGINS, self.MARGINS, self.MARGINS
        )

        self.scroll.setWidget(self.content_widget)

        self.overlay_container = overlay.Overlay(
            self.scroll, height_percentage=0.8
        )
        self.overlay_container.setVisible(False)

    def post_build(self):
        '''post build function , mostly used connect widgets events.'''
        self.widget.clicked.connect(self.show_widget)

    def show_widget(self):
        '''Show the progress widget overlay'''
        main_window = utils.get_main_framework_window_from_widget(self.widget)
        if main_window:
            self.overlay_container.setParent(main_window)
        self.overlay_container.setVisible(True)
        self.widget.setVisible(True)

    def hide_widget(self):
        self.widget.setVisible(False)

    # Thread safe entry points

    def prepare_add_steps(self):
        '''Prepare the progress widget to add steps(components)'''
        self.clear_components()
        self.status_banner = StatusButtonWidget(
            StatusButtonWidget.VIEW_EXPANDED_BANNER
        )
        self.content_widget.layout().addWidget(self.status_banner)

    def add_step(
        self, step_type, step_name, batch_id=None, label=None, indent=0
    ):
        '''Add a step(component) to the progress widget'''
        id_name = "{}.{}.{}".format(batch_id or '-', step_type, step_name)
        step_button = PhaseButton(label or step_name, "Not started")
        self._step_widgets[id_name] = step_button
        self.content_widget.layout().setContentsMargins(
            self.MARGINS + indent * 10,
            self.MARGINS,
            self.MARGINS,
            self.MARGINS,
        )
        if step_type not in self.step_types:
            self.step_types.append(step_type)
            step_title = QtWidgets.QLabel(step_type.upper())
            step_title.setObjectName("gray")
            self.content_widget.layout().addWidget(step_title)
        self.content_widget.layout().addWidget(step_button)

    def widgets_added(self, button=None):
        '''All widgets have been added to the progress widget'''
        self.content_widget.layout().addWidget(QtWidgets.QLabel(), 10)
        if button:
            self.content_widget.layout().addWidget(button)

    def clear_components(self):
        for i in reversed(range(self.content_widget.layout().count())):
            if self.content_widget.layout().itemAt(i).widget():
                self.content_widget.layout().itemAt(i).widget().deleteLater()
        self.step_types = []
        self._step_widgets = {}

    def set_status(self, status, message=None):
        self.widget.set_status(status, message=message)
        if self.status_banner:
            self.status_banner.set_status(status, message=message)
        self.set_status_widget_visibility(True)

    def set_status_widget_visibility(self, visibility=False):
        self.widget.setVisible(visibility)

    def update_step_status(
        self, step_type, step_name, status, status_message, results, batch_id
    ):
        '''Update the status of the progress of a step/component'''
        id_name = "{}.{}.{}".format(batch_id or '-', step_type, step_name)
        if id_name in self._step_widgets:
            self._step_widgets[id_name].update_status(
                status, status_message, results
            )
            if status != self.widget.get_status():
                main_status_message = '{}{}.{}: {}'.format(
                    ('{}.'.format(batch_id)) if batch_id else '',
                    step_type,
                    step_name,
                    status_message,
                )
                self.widget.set_status(status, message=main_status_message)
                if self.status_banner:
                    self.status_banner.set_status(
                        status, message=main_status_message
                    )

    def reset_statuses(self, status="Not started", status_message=''):
        '''Reset statuses of all progress steps'''
        for step_widget in self._step_widgets.values():
            step_widget.update_status(status, status_message, None)


class BatchProgressWidget(ProgressWidgetObject):
    '''Progress widget designed for batch processing multiple assets'''

    def __init__(
        self, name, fragment_data, status_view_mode=None, parent=None
    ):
        super(BatchProgressWidget, self).__init__(
            name,
            fragment_data,
            status_view_mode=status_view_mode,
            parent=parent,
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

    def add_item(self, item):
        item_widget = QtWidgets.QLabel(item)
        item_widget.setObjectName('h2')
        self.content_widget.layout().addWidget(item_widget)
