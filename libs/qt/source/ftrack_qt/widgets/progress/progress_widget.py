import logging

from Qt import QtWidgets

import ftrack_constants as constants

from ftrack_qt.utils.layout import recursive_clear_layout
from ftrack_qt.widgets.overlay import OverlayWidget
from ftrack_qt.widgets.buttons import (
    ProgressStatusButtonWidget,
    ProgressPhaseButtonWidget,
)
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


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

        self._overlay_container = None
        self._content_widget = None
        self._status_banner = None
        self._status_widget = None
        self._scroll = None
        self._categories = []
        self._phase_widgets = {}
        self._main_window = None
        self._action = action

        self.logger = logging.getLogger(__name__)

        self.build()
        self.post_build()

        self.set_data(data)

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
        self.status_widget.clicked.connect(self.show_overlay)

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
            self._phase_widgets[id_] = phase_button
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

        self._content_widget.layout().addWidget(QtWidgets.QLabel(), 10)

    def _set_status_widget_visibility(self, visibility=False):
        '''Update the visibility of the progress widget'''
        self.status_widget.setVisible(visibility)

    def show_overlay(self, main_window=None):
        '''Show the progress widget overlay on top of *main_window*'''
        if main_window:
            self._main_window = main_window
            self._overlay_container.setParent(self._main_window)
        self._overlay_container.setVisible(True)
        self.status_widget.setVisible(True)

    def hide_overlay(self):
        '''Hide the progress widget'''
        self.status_widget.setVisible(False)

    # Run
    def reset_statuses(self, new_status=None, status_message=''):
        '''Reset statuses of all progress phases'''
        if not new_status:
            new_status = constants.status.UNKNOWN_STATUS
        for phase_widget in list(self._phase_widgets.values()):
            phase_widget.update_status(new_status, status_message, None)
            phase_widget.hide_log()

    @invoke_in_qt_main_thread
    def run(self, main_widget):
        '''Run progress widget on top of *main_widget*, with *action*'''
        self.reset_statuses()
        self.update_status(
            constants.status.RUNNING_STATUS,
            message=f'Running {self.action.lower()}...',
        )
        self.show_overlay(main_widget)

    def update_status(self, new_status, message=None):
        '''Set the new main status to *new_status*, with optional *message*'''
        self.logger.debug(
            f'Main status update: {new_status} (message: {message})'
        )
        self.status_widget.set_status(new_status, message=message)
        if self._status_banner:
            self._status_banner.set_status(new_status, message=message)
        self._set_status_widget_visibility(True)

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
