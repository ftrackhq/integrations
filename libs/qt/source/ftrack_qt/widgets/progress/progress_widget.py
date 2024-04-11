import logging

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

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

    hide_overlay_signal = QtCore.Signal()
    show_overlay_signal = QtCore.Signal()

    @property
    def overlay_widget(self):
        '''Return the status widget'''
        return self._overlay_widget

    @property
    def status_widget(self):
        '''Return the status widget'''
        return self._status_widget

    @property
    def status(self):
        '''Return the overall progress widget status'''
        return self.status_widget.status

    @property
    def action(self):
        '''Return a descriptive name of the action that is being run'''
        return self._action or ''

    def __init__(self, action, data, parent=None):
        '''Initialise ProgressWidgetObject with *action* describing what progress
        represents and *data* containing information about the progress phases,
        with ptional *parent*'''

        super(ProgressWidget, self).__init__(parent=parent)

        self._overlay_widget = None
        self._progress_area = None
        self._status_widget = None

        self._action = action

        self.logger = logging.getLogger(__name__)

        self.build()
        self.post_build()

        self.set_data(data)

    def build(self):
        self._status_widget = ProgressStatusButtonWidget('header-button')
        self._status_widget.setVisible(False)

        self._overlay_widget = OverlayWidget()

        self._progress_area = ProgressArea()
        self._progress_area.set_action(self.action)

        self._overlay_widget.set_widget(self._progress_area)

    def post_build(self):
        '''Wire up signals'''
        self.status_widget.clicked.connect(self._on_status_widget_clicked)
        self.overlay_widget.close_button_clicked.connect(
            self._on_overlay_close
        )
        self._progress_area.status_updated.connect(self._on_status_updated)

    def set_data(self, data):
        '''Set the data for the progress widget, were *data* is a list of
        dictionaries, one for each progress phase, with the following keys:
            - id: Unique id of the phase
            - label: A label for the phase
            - category: (optional) The category of the phase
            - tags: (optional) A list of tags for the phase
            - indent: (optional) The indent level of the phase
        '''
        self._progress_area.set_data(data)

    def _on_status_widget_clicked(self):
        '''Emits a signal when status widget is clicked'''
        self.show_overlay_signal.emit()

    def _on_overlay_close(self):
        '''Calls the hide overlay function when overlay close button is clicked'''
        '''Hide the progress widget'''
        self.hide_overlay()

    def hide_overlay(self):
        '''Hide the progress widget'''
        self.hide_overlay_signal.emit()

    # Run
    def run(self):
        '''Run progress widget on top of *main_widget*, with *action*'''
        self._progress_area.reset_phase_statuses()
        self.update_status(
            constants.status.RUNNING_STATUS,
            message=f'Running {self.action.lower()}...',
        )

    def update_status(self, new_status, message=None):
        '''Set the new main status to *new_status*, with optional *message*'''
        self.logger.debug(
            f'Main status update: {new_status} (message: {message})'
        )
        self._progress_area.update_status(new_status, message)

    def _on_status_updated(self, new_status, message):
        '''Method clall when status updated from progress area'''
        self.status_widget.set_status(new_status, message=message)
        self.status_widget.setVisible(True)

    def update_phase_status(
        self,
        id_,
        new_status,
        log_message='',
        status_message=None,
        time=None,
    ):
        '''Update the status of a phase/plugin *id_* to *new_status*, with
        optional *log_message*, *status_message* and execution *time*'''
        self._progress_area.update_phase_status(
            id_, new_status, log_message, status_message, time
        )

    def teardown(self):
        '''Teardown the progress widget - properly cleanup the overlay containers'''
        self._progress_area.teardown()


class ProgressArea(QtWidgets.QScrollArea):
    '''
    Representation of all the execution phases on a scroll area
    '''

    status_updated = QtCore.Signal(object, object)

    @property
    def content_widget(self):
        '''Return the status widget'''
        return self._content_widget

    @property
    def action(self):
        '''Return a descriptive name of the action that is being run'''
        return self._action or ''

    @property
    def status(self):
        '''Return a descriptive name of the action that is being run'''
        return self._status or ''

    def __init__(self, parent=None):
        '''Initialise ProgressWidgetObject with *action* describing what progress
        represents and *data* containing information about the progress phases,
        with ptional *parent*'''

        super(ProgressArea, self).__init__(parent=parent)

        self._content_widget = None
        self._content_widget_layout = None
        self._stacked_widget = None
        self._status_banner = None

        self._categories = []
        self._phase_widgets = {}

        self._action = None
        self._status = None

        self.logger = logging.getLogger(__name__)

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self.setWidgetResizable(True)

    def build(self):
        self._stacked_widget = QtWidgets.QStackedWidget()

        self._content_widget = QtWidgets.QFrame()
        self._content_widget.setObjectName('overlay')
        self._content_widget_layout = QtWidgets.QVBoxLayout()
        self._content_widget.setLayout(self._content_widget_layout)

        self._content_widget.setLayout(self._content_widget_layout)

        # Add widgets to the stacked widget
        self._stacked_widget.addWidget(self._content_widget)

        self.setWidget(self._stacked_widget)
        self._stacked_widget.setCurrentIndex(0)

    def set_action(self, action):
        '''Sets action name'''
        self._action = action

    def set_data(self, data):
        '''Set the data for the progress widget, were *data* is a list of
        dictionaries, one for each progress phase, with the following keys:
            - id: Unique id of the phase
            - label: A label for the phase
            - category: (optional) The category of the phase
            - tags: (optional) A list of tags for the phase
            - indent: (optional) The indent level of the phase
        '''
        assert data and isinstance(data, list), 'Data must be a list'

        recursive_clear_layout(self._content_widget.layout())

        self._status_banner = ProgressStatusButtonWidget('overlay-banner')
        self._content_widget.layout().addWidget(self._status_banner)

        self._categories = []
        self._phase_widgets = {}

        for phase_data in data:
            assert phase_data.get(
                'id'
            ), 'ID must be defined with progress widget phase!'
            assert phase_data.get(
                'label'
            ), 'Label must be defined with progress widget phase!'

            id_ = phase_data['id']
            label = phase_data['label']
            category = phase_data.get('category', '')
            tags = phase_data.get('tags')
            indent = phase_data.get('indent', 0)

            phase_button = ProgressPhaseButtonWidget(
                label, category=category, tags=tags
            )
            phase_button.hide_overlay_signal.connect(self.show_main_widget)
            phase_button.show_overlay_signal.connect(self.show_overlay_widget)
            self._phase_widgets[id_] = phase_button
            if category not in self._categories:
                self._categories.append(category)
                phase_category = QtWidgets.QLabel(category)
                phase_category.setObjectName("gray")
                self._content_widget.layout().addWidget(phase_category)
            self._content_widget.layout().addWidget(phase_button)

        self._content_widget.layout().addWidget(QtWidgets.QLabel(), 10)

    def show_main_widget(self):
        '''Show the main widget index 0 of stacked widget'''
        self._stacked_widget.setCurrentIndex(0)

    def show_overlay_widget(self, widget):
        '''Sets the given *widget* as the index 1 of the stacked widget and
        remove the previous one if it exists'''
        if self._stacked_widget.widget(1):
            self._stacked_widget.removeWidget(self._stacked_widget.widget(1))
        self._stacked_widget.addWidget(widget)
        self._stacked_widget.setCurrentIndex(1)

    # Run

    def reset_phase_statuses(self, new_status=None, status_message=''):
        '''Reset statuses of all progress phases'''
        if not new_status:
            new_status = constants.status.UNKNOWN_STATUS
        for phase_widget in list(self._phase_widgets.values()):
            phase_widget.update_status(new_status, status_message, None)

    def update_status(self, new_status, message=None):
        '''Set the new main status to *new_status*, with optional *message*'''
        if self._status_banner:
            self._status_banner.set_status(new_status, message=message)
        self._status = new_status
        self.status_updated.emit(new_status, message)

    def update_phase_status(
        self,
        id_,
        new_status,
        log_message='',
        status_message=None,
        time=None,
    ):
        '''Update the status of a phase/plugin *id_* to *new_status*, with
        optional *log_message*, *status_message* and execution *time*'''
        self.logger.debug(
            f'Phase {id_} status update: {new_status} (message: {log_message}'
        )
        assert id_, 'Widget ID cannot be None'
        assert new_status, 'Status cannot be None'
        if not status_message:
            status_message = (
                constants.status.STATUS_STRING_MAPPING.get(new_status)
                or new_status
            )

        if id_ in self._phase_widgets:
            phase_widget = self._phase_widgets[id_]
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
                f'Progress phase widget with ID {id_} not found!'
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

    def teardown(self):
        '''Teardown the progress widget - properly cleanup the overlay containers'''
        for phase_widget in list(self._phase_widgets.values()):
            phase_widget.deleteLater()
