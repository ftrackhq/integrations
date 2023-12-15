import logging

from Qt import QtWidgets, QtCore

import ftrack_constants as constants

from ftrack_qt.utils.layout import recursive_clear_layout
from ftrack_qt.widgets.overlay import OverlayWidget
from ftrack_qt.widgets.buttons import (
    ProgressStatusButtonWidget,
    ProgressPhaseButtonWidget,
)


class ProgressWidget(QtWidgets.QWidget):
    '''
    Widget representation of the progress overlay widget used during execution of a
    lengthy proces that needs to visualize status updates and provide log
    feedback.

    The widget is composed of a dialog header docked button widget and info button
    widget representing main status. Main area is a  scroll area containing detailed
    progress feedback in form of phases (plugin runs) grouped into categories
    (context, collector...).

    '''

    MARGINS = 15

    STATUS_MAPPINGS = {
        constants.status.UNKNOWN_STATUS: 'Not started',
        constants.status.SUCCESS_STATUS: 'Success',
        constants.status.WARNING_STATUS: 'Warning',
        constants.status.ERROR_STATUS: 'ERROR',
        constants.status.EXCEPTION_STATUS: 'EXCEPTION',
        constants.status.RUNNING_STATUS: 'Running',
        constants.status.DEFAULT_STATUS: 'Pause',
    }

    _phase_widgets = {}

    @property
    def button_widget(self):
        '''Return the button widget'''
        return self._status_widget

    @property
    def status(self):
        '''Return the overall progress widget status'''
        return self.button_widget.status

    @property
    def action(self):
        '''Return a descriptive name of the action that is being run'''
        return self._action or ''

    def __init__(self, parent=None):
        '''Initialise ProgressWidgetObject with optional *parent*'''

        super(ProgressWidget, self).__init__(parent=parent)

        self._overlay_container = None
        self._content_widget = None
        self._status_banner = None
        self._status_widget = None
        self._scroll = None
        self._categories = []
        self._main_window = None
        self._action = None

        self.logger = logging.getLogger(__name__)

        self.build()
        self.post_build()

    def build(self):
        self._status_widget = ProgressStatusButtonWidget('header-button')
        self._set_status_widget_visibility(False)

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

    def prepare_add_phases(self):
        '''Prepare the progress widget to add phases'''
        self._clear_components()
        self._status_banner = ProgressStatusButtonWidget('overlay-banner')
        self._content_widget.layout().addWidget(self._status_banner)

    def has_phase_widget(self, reference):
        '''Return True if a phase widget with *reference* exists'''
        return reference in self._phase_widgets

    def add_phase_widget(
        self,
        reference,
        category,
        label,
        indent=0,
    ):
        '''Add progress widget representation for phase having unique *reference*
        (string), beneath *category*, having *label*.

        Optional *indent* defines left margin.
        '''
        if self.has_phase_widget(reference):
            raise ValueError(
                'Phase widget with reference {} already exists'.format(
                    reference
                )
            )
        phase_button = ProgressPhaseButtonWidget(category, label)
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

    def phases_added(self):
        '''All widgets have been added to the progress widget'''
        self._content_widget.layout().addWidget(QtWidgets.QLabel(), 10)

    def _clear_components(self):
        recursive_clear_layout(self._content_widget.layout())
        self._categories = []
        self._phase_widgets = {}

    def _set_status_widget_visibility(self, visibility=False):
        '''Update the visibility of the progress widget'''
        self.button_widget.setVisible(visibility)

    def show_widget(self, main_window=None):
        '''Show the progress widget overlay on top of *main_window*'''
        if main_window:
            self._main_window = main_window
            self._overlay_container.setParent(self._main_window)
        self._overlay_container.setVisible(True)
        self.button_widget.setVisible(True)

    def hide_widget(self):
        '''Hide the progress widget'''
        self.button_widget.setVisible(False)

    # Run
    def reset_statuses(self, new_status=None, status_message=''):
        '''Reset statuses of all progress phases'''
        if not new_status:
            new_status = constants.status.UNKNOWN_STATUS
        for phase_widget in self._phase_widgets.values():
            phase_widget.update_status(new_status, status_message, None)

    def run(self, main_widget, action):
        '''Run progress widget on top of *main_widget*, with *action*'''
        self._action = action
        self.reset_statuses()
        self.update_status(
            constants.status.RUNNING_STATUS,
            message=f'Running {self.action.lower()}...',
        )
        self.show_widget(main_widget)

    def update_status(self, new_status, message=None):
        '''Set the new main status to *new_status*, with optional *message*'''
        self.logger.debug(
            f'Main status update: {new_status} (message: {message}'
        )
        self.button_widget.set_status(new_status, message=message)
        if self._status_banner:
            self._status_banner.set_status(new_status, message=message)
        self._set_status_widget_visibility(True)

    def update_phase_status(
        self,
        reference,
        new_status,
        log_message='',
        status_message=None,
        time=None,
    ):
        '''Update the status of a phase/plugin *reference* to *new_status*, with
        optional *log_message*, *status_message* and execution *time*'''
        self.logger.debug(
            f'Phase {reference} status update: {new_status} (message: {log_message}'
        )
        assert reference, 'Reference cannot be None'
        assert new_status, 'Status cannot be None'
        if not status_message:
            status_message = self.STATUS_MAPPINGS.get(new_status) or new_status

        if reference in self._phase_widgets:
            phase_widget = self._phase_widgets[reference]
            phase_widget.update_status(
                new_status, status_message, log_message, time=time
            )
            main_status_message = (
                f'{phase_widget.category}.'
                f'{phase_widget.text()}: {status_message}'
            )
            self.update_status(self.status, message=main_status_message)

        else:
            self.logger.warning(
                'No phase widget found for {}'.format(reference)
            )

        # Error or finished?
        if new_status in [
            constants.status.ERROR_STATUS,
            constants.status.EXCEPTION_STATUS,
        ]:
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
        elif new_status == constants.status.SUCCESS_STATUS:
            finished = True
            for ref, widget in list(self._phase_widgets.items()):
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
        self.update_phase_status(
            log_item.plugin_reference,
            log_item.plugin_status,
            log_message=log_item.plugin_message,
            time=log_item.plugin_execution_time,
        )
