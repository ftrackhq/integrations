# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import shiboken2
import logging

from Qt import QtWidgets, QtCore

from ftrack_constants.framework import status
from ftrack_utils.threading import is_main_thread

from ftrack_qt.utils.layout import recursive_clear_layout
from ftrack_qt.utils.widget import set_property
from ftrack_qt.widgets.overlay import OverlayWidget
from ftrack_qt.widgets.icons import StatusMaterialIconWidget

import ftrack_constants.framework as constants


class ProgressWidget(QtWidgets.QWidget):
    '''
    Widget representation of the progress overlay widget used during dialog run.

    The widget is composed of a main button widget representing status of entire tool
     process, and a scroll area containing detailed progress feedback in form of phases
     categorized in phase types (context, components, finalizers).

     Additional batch processing is supported, to allow progress of multiple operations to
     be tracked.
    '''

    MARGINS = 15
    NOT_STARTED_STATUS = 'Not started'

    _phase_widgets = {}

    @property
    def button_widget(self):
        '''Return the button widget'''
        return self._button_widget

    @property
    def status(self):
        '''Return the overall progress widget status'''
        return self.button_widget.status

    @property
    def last_status(self):
        '''Return the most recent phase status'''
        return self._last_status

    @property
    def action(self):
        return self._action or ''

    @action.setter
    def action(self, value):
        self._action = value

    def __init__(self, status_view_mode=None, parent=None):
        '''Initialise ProgressWidgetObject with optional *status_view_mode* and *parent*'''

        super(ProgressWidget, self).__init__(parent=parent)
        self._status_view_mode = status_view_mode

        self._overlay_container = None
        self._content_widget = None
        self._status_banner = None
        self._button_widget = None
        self._scroll = None
        self._categories = []
        self._last_status = None
        self._main_window = None
        self._action = None

        self.logger = logging.getLogger(__name__)

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        pass

    def build(self):
        self._button_widget = ProgressStatusButtonWidget(
            self._status_view_mode
        )
        self.set_status_widget_visibility(False)

        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self._scroll.setWidgetResizable(True)

        self._content_widget = QtWidgets.QFrame()
        self._content_widget.setObjectName('overlay')
        self._content_widget.setLayout(QtWidgets.QVBoxLayout())
        self._content_widget.layout().setContentsMargins(
            self.MARGINS, self.MARGINS, self.MARGINS, self.MARGINS
        )

        self._scroll.setWidget(self._content_widget)

        self._overlay_container = OverlayWidget(
            self._scroll, height_percentage=0.8
        )
        self._overlay_container.setVisible(False)

    def post_build(self):
        '''Wire up signals'''
        self.button_widget.clicked.connect(self.show_widget)

    # Build

    def prepare_add_phases(self):
        '''Prepare the progress widget to add phases'''
        self._clear_components()
        self._status_banner = ProgressStatusButtonWidget(
            ProgressStatusButtonWidget.VIEW_EXPANDED_BANNER
        )
        self._content_widget.layout().addWidget(self._status_banner)

    def add_phase_widget(
        self,
        reference,
        category,
        label,
        indent=0,
    ):
        '''Add progress widget representation for widget having unique *reference*
        (string), beneath *category*, having *label*.

        Optional *indent* defines left margin.
        '''
        phase_button = ProgressPhaseButtonWidget(
            category, label, ProgressWidget.NOT_STARTED_STATUS
        )
        self._phase_widgets[reference] = phase_button
        self._content_widget.layout().setContentsMargins(
            self.MARGINS + indent * 10,
            self.MARGINS,
            self.MARGINS,
            self.MARGINS,
        )
        if category not in self._categories:
            self._categories.append(category)
            phase_category = QtWidgets.QLabel(category)
            phase_category.setObjectName("gray")
            self._content_widget.layout().addWidget(phase_category)
        self._content_widget.layout().addWidget(phase_button)

    def phases_added(self, button=None):
        '''All widgets have been added to the progress widget'''
        self._content_widget.layout().addWidget(QtWidgets.QLabel(), 10)
        if button:
            self._content_widget.layout().addWidget(button)

    def _clear_components(self):
        recursive_clear_layout(self._content_widget.layout())
        self._categories = []
        self._phase_widgets = {}

    def set_status_widget_visibility(self, visibility=False):
        '''Update the visibility of the progress widget'''
        self.button_widget.setVisible(visibility)

    def show_widget(self, main_window=None):
        '''Show the progress widget overlay on top of *main_window*'''
        if main_window:
            self._main_window = main_window
        if self._main_window:
            self._overlay_container.setParent(self._main_window)
        self._overlay_container.setVisible(True)
        self.button_widget.setVisible(True)

    def hide_widget(self):
        self.button_widget.setVisible(False)

    # Run
    def reset_statuses(self, new_status=None, status_message=''):
        '''Reset statuses of all progress phases'''
        if new_status is None:
            new_status = ProgressWidget.NOT_STARTED_STATUS
        for phase_widget in self._phase_widgets.values():
            phase_widget.update_status(new_status, status_message, None)

    def update_status(self, new_status, message=None):
        '''Set the new overall status to *new_status*, with optional *message*'''
        self.button_widget.set_status(new_status, message=message)
        if self._status_banner:
            self._status_banner.set_status(new_status, message=message)
        self.set_status_widget_visibility(True)

    def run(self, main_widget, action):
        '''Run progress widget, with *action*'''
        self.action = action
        self.reset_statuses()
        self.update_status(
            constants.status.RUNNING_STATUS,
            message=f'Running {self.action.lower()}...',
        )
        self.show_widget(main_widget)

    def update_phase_status(
        self,
        reference,
        new_status,
        log_message='',
        status_message=None,
        time=None,
    ):
        '''Update the status of a phase *phase_name* under *category* to *new_status*, with
        optional *status_message* and *log*'''
        assert reference, 'Reference cannot be None'
        assert new_status, 'Status cannot be None'
        if not status_message:
            status_message = ''
            if new_status == status.SUCCESS_STATUS:
                status_message = 'Success'
            elif new_status == status.RUNNING_STATUS:
                status_message = 'Running'
            elif new_status == status.ERROR_STATUS:
                status_message = 'ERROR'
            elif new_status == status.EXCEPTION_STATUS:
                status_message = 'EXCEPTION'

        if reference in self._phase_widgets:
            phase_widget = self._phase_widgets[reference]
            phase_widget.update_status(
                new_status, status_message, log_message, time=time
            )
            main_status_message = '{}.{}: {}'.format(
                phase_widget.category,
                phase_widget.text(),
                status_message,
            )
            self.update_status(self.status, message=main_status_message)

            self._last_status = new_status

        else:
            self.logger.warning(
                'No phase widget found for {}'.format(reference)
            )

        # Error or finished?
        if new_status in [status.ERROR_STATUS, status.EXCEPTION_STATUS]:
            # Failed, reflect on main status
            if new_status == constants.status.ERROR_STATUS:
                self.update_status(
                    constants.status.ERROR_STATUS,
                    message=f'{self.action.title()} failed, see logs for details.',
                )
            elif new_status == constants.status.ERROR_STATUS:
                self.update_status(
                    constants.status.EXCEPTION_STATUS,
                    message=f'{self.action.title()} CRASHED, see logs for details.',
                )
        elif new_status == status.SUCCESS_STATUS:
            finished = True
            for widget in list(self._phase_widgets.values()):
                if widget.status != constants.status.SUCCESS_STATUS:
                    finished = False
                    break
            if finished:
                self.update_status(
                    constants.status.SUCCESS_STATUS,
                    message=f'{self.action.title()} completed successfully',
                )

    def update_framework_progress(self, log_item):
        '''A framework plugin has been executed, with information passed on in *log_item*'''
        self.logger.debug(
            "Progress: \n "
            "  plugin_name: {} \n"
            "  plugin_status: {} \n"
            "  plugin_message: {} \n"
            "  plugin_execution_time: {} \n"
            "  plugin_store: {} \n".format(
                log_item.plugin_name,
                log_item.plugin_status,
                log_item.plugin_message,
                log_item.plugin_execution_time,
                log_item.plugin_options,
                log_item.plugin_store,
            )
        )
        self.update_phase_status(
            log_item.plugin_reference,
            log_item.plugin_status,
            log_message=log_item.plugin_message,
            time=log_item.plugin_execution_time,
        )


class ProgressStatusButtonWidget(QtWidgets.QPushButton):
    '''Progress main status button representation, to be put inside the
    tool header.'''

    # Button view modes
    VIEW_COLLAPSED_BUTTON = 'collapsed-button'  # AM (Opens progress overlay)
    VIEW_EXPANDED_BUTTON = 'expanded-button'  # Opener/Assembler/Publisher (Opens progress overlay)
    VIEW_EXPANDED_BANNER = 'expanded-banner'  # Progress overlay

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def __init__(self, view_mode, parent=None):
        super(ProgressStatusButtonWidget, self).__init__(parent=parent)

        self._status = None
        self._view_mode = view_mode or self.VIEW_EXPANDED_BUTTON

        self._message_label = None
        self._status_icon = None

        self.pre_build()
        self.build()

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(1)
        self.setLayout(layout)

        self.setMinimumHeight(32)
        if self._view_mode == self.VIEW_COLLAPSED_BUTTON:
            self.setMaximumHeight(32)
            self.setMinimumWidth(32)
            self.setMaximumWidth(32)
        else:
            self.setMinimumWidth(200)

    def build(self):
        self.setObjectName('status-widget-{}'.format(self._view_mode))

        self._message_label = QtWidgets.QLabel()
        self.layout().addWidget(self._message_label)
        self.layout().addStretch()
        self._status_icon = StatusMaterialIconWidget('')
        self.layout().addWidget(self._status_icon)

        self.set_status(status.SUCCESS_STATUS)

    def set_status(self, new_status, message=''):
        self.status = new_status or status.DEFAULT_STATUS
        self.message = message
        self._message_label.setText(self.message)
        set_property(self, 'status', self._status.lower())
        color = self._status_icon.set_status(self.status, size=24)
        self._message_label.setStyleSheet('color: #{}'.format(color))


class ProgressPhaseButtonWidget(QtWidgets.QPushButton):
    '''Showing progress of a progress phase, when pressed the log is shown.'''

    @property
    def category(self):
        return self._category

    @property
    def label(self):
        return self.text()

    @property
    def status(self):
        return self._status

    @property
    def log_message(self):
        return self._log_message

    @log_message.setter
    def log_message(self, value):
        '''Store for log *value* for view and set it as tooltip'''
        self._log_message = value
        self.setToolTip(value or '')

    def __init__(self, category, label, status, parent=None):
        '''Instantiate the PhaseButtonWidget with *label* and *status*'''

        super(ProgressPhaseButtonWidget, self).__init__(parent=parent)

        self._category = category
        self._label = label
        self._status = status or constants.status.DEFAULT_STATUS
        self._log = None

        self._icon_widget = None
        self._status_message_widget = None
        self._log_message_widget = None
        self._log_text_edit = None
        self._close_button = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.setMinimumHeight(
            32
        )  # Set minimum otherwise it will collapse the container
        self.setMinimumWidth(200)
        self.layout().setContentsMargins(3, 3, 3, 3)

    def build(self):
        self._icon_widget = StatusMaterialIconWidget(None)
        self.layout().addWidget(self._icon_widget)
        self.set_status(self.status)
        set_property(self, 'status', self.status.lower())

        v_layout = QtWidgets.QVBoxLayout()

        label_widget = QtWidgets.QLabel(self._label)
        label_widget.setObjectName('h3')
        v_layout.addWidget(label_widget)

        self._status_message_widget = QtWidgets.QLabel(self._status)
        self._status_message_widget.setObjectName('gray')
        v_layout.addWidget(self._status_message_widget)

        self.layout().addLayout(v_layout, 100)

        self._time_widget = QtWidgets.QLabel()
        self._time_widget.setObjectName('gray')
        self.layout().addWidget(self._time_widget)

        self._log_message_widget = QtWidgets.QFrame()
        self._log_message_widget.setVisible(False)
        self._log_message_widget.setLayout(QtWidgets.QVBoxLayout())
        self._log_message_widget.layout().addSpacing(10)

        self._log_text_edit = QtWidgets.QTextEdit()
        self._log_text_edit.setReadOnly(True)
        self._log_message_widget.layout().addWidget(self._log_text_edit, 10)
        self._close_button = QtWidgets.QPushButton('HIDE LOG')
        self._log_message_widget.layout().addWidget(self._close_button)
        self._log_overlay = OverlayWidget(self._log_message_widget)
        self._log_overlay.setVisible(False)

    def post_build(self):
        self.clicked.connect(self.show_log)
        self._close_button.clicked.connect(self._log_overlay.close)

    def update_status(
        self, new_status, status_message, log_message, time=None
    ):
        '''Update the status of the phase to *new_status* and set *status_message*. 
        Build log messages from *log*.''' ''
        # Make sure widget not has been destroyed
        color = self.set_status(new_status)
        if shiboken2.isValid(self._status_message_widget):
            self._status_message_widget.setText(status_message)
            self._status_message_widget.setStyleSheet(
                'color: #{};'.format(color)
            )
            if time:
                self._time_widget.setText(f'{time:.3f}s')
            else:
                self._time_widget.setText('')
        self.log_message = log_message

    def set_status(self, new_status):
        '''Visualize *new_status* on the button'''
        set_property(self, 'status', new_status.lower())
        return self._icon_widget.set_status(new_status)

    def show_log(self):
        self._log_overlay.setParent(self.parent())
        if len(self.log_message or '') > 0:
            self._log_text_edit.setText(self.log_message)
        else:
            self._log_text_edit.setText("No errors found")
        self._log_overlay.setVisible(True)
        self._log_message_widget.setVisible(True)
        self._log_overlay.resize(self.parent().size())
