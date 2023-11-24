# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import shiboken2

from Qt import QtWidgets, QtCore

from ftrack_constants.framework import status
from ftrack_utils.threading import is_main_thread

from ftrack_qt.utils.layout import recursive_clear_layout
from ftrack_qt.utils.widget import set_property
from ftrack_qt.widgets.overlay import OverlayWidget
from ftrack_qt.widgets.icons import StatusMaterialIconWidget


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

    _update_status_async = QtCore.Signal(object, object)
    # Delegate to main thread - update overall status based on status and message

    _update_phase_status_async = QtCore.Signal(
        object, object, object, object, object, object
    )
    # Delegate to main thread - update status based on category, phase name, status, message, log and batch id

    @property
    def button_widget(self):
        '''Return the button widget'''
        return self._button_widget

    def __init__(self, status_view_mode=None, parent=None):
        '''Initialise ProgressWidgetObject with optional *status_view_mode* and *parent*'''

        super(ProgressWidget, self).__init__(parent=parent)
        self._status_view_mode = status_view_mode

        self._content_widget = None
        self._status_banner = None
        self._button_widget = None
        self._scroll = None
        self._categories = []

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        pass

    def build(self):
        self._button_widget = StatusButtonWidget(self._status_view_mode)
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
        '''post build function , mostly used connect widgets events.'''
        self.button_widget.clicked.connect(self.show_widget)
        self._update_status_async.connect(self.update_status)
        self._update_phase_status_async.connect(self.update_phase_status)

    # Build

    def prepare_add_phases(self):
        '''Prepare the progress widget to add phases'''
        self._clear_components()
        self._status_banner = StatusButtonWidget(
            StatusButtonWidget.VIEW_EXPANDED_BANNER
        )
        self._content_widget.layout().addWidget(self._status_banner)

    def add_phase(
        self, category, phase_name, batch_id=None, phase_label=None, indent=0
    ):
        '''Add a phase *phase_name* for *batch_id* to the progress widget, under *category*
        having optional label *phase_label* and optional *indent* left margin
        '''
        id_name = "{}.{}.{}".format(batch_id or '-', category, phase_name)
        phase_button = PhaseButtonWidget(
            phase_label or phase_name, ProgressWidget.NOT_STARTED_STATUS
        )
        self._phase_widgets[id_name] = phase_button
        self._content_widget.layout().setContentsMargins(
            self.MARGINS + indent * 10,
            self.MARGINS,
            self.MARGINS,
            self.MARGINS,
        )
        if category not in self._categories:
            self._categories.append(category)
            phase_category = QtWidgets.QLabel(category.upper())
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

    # Run

    def reset_statuses(self, new_status=None, status_message=''):
        '''Reset statuses of all progress phases'''
        if new_status is None:
            new_status = ProgressWidget.NOT_STARTED_STATUS
        for phase_widget in self._phase_widgets.values():
            phase_widget.update_status(new_status, status_message, None)

    def update_status(self, new_status, message=None):
        '''Set the new overall status to *new_status*, with optional *message*'''
        if not is_main_thread():
            self._update_status_async.emit(new_status, message)
            return
        self.button_widget.set_status(new_status, message=message)
        if self._status_banner:
            self._status_banner.set_status(new_status, message=message)
        self.set_status_widget_visibility(True)

    def set_status_widget_visibility(self, visibility=False):
        '''Update the visibility of the progress widget'''
        self.button_widget.setVisible(visibility)

    def show_widget(self, main_window):
        '''Show the progress widget overlay on top of *main_window*'''
        if main_window:
            self._overlay_container.setParent(main_window)
        self._overlay_container.setVisible(True)
        self.button_widget.setVisible(True)

    def hide_widget(self):
        self.button_widget.setVisible(False)

    def update_phase_status(
        self, category, phase_name, new_status, status_message, log, batch_id
    ):
        '''Update the status of a phase *phase_name* under *category* to *new_status*, with
        optional *status_message* and *log* for optional *batch_id*'''
        if not is_main_thread():
            self._update_phase_status_async.emit(
                category,
                phase_name,
                new_status,
                status_message,
                log,
                batch_id,
            )
            return
        id_name = "{}.{}.{}".format(batch_id or '-', category, phase_name)
        if id_name in self._phase_widgets:
            self._phase_widgets[id_name].update_status(
                new_status, status_message, log
            )
            if new_status != self.button_widget.status:
                main_status_message = '{}{}.{}: {}'.format(
                    ('{}.'.format(batch_id)) if batch_id else '',
                    category,
                    phase_name,
                    status_message,
                )
                self.button_widget.set_status(
                    new_status, message=main_status_message
                )
                if self._status_banner:
                    self._status_banner.set_status(
                        new_status, message=main_status_message
                    )


class PhaseButtonWidget(QtWidgets.QPushButton):
    '''Showing progress of a progress phase, when pressed the log is shown.'''

    @property
    def log(self):
        return self._log

    @log.setter
    def log(self, value):
        '''Store for log *value* for view and set it as tooltip'''
        self._log = value
        self.setToolTip(value or '')

    def __init__(self, phase_name, phase_status, parent=None):
        '''Instantiate the PhaseButtonWidget with *phase_name* and *phase_status*'''

        super(PhaseButtonWidget, self).__init__(parent=parent)

        self._phase_name = phase_name
        self._status = phase_status
        self._log = None

        self._icon_widget = None
        self._status_message_widget = None
        self._log_widget = None
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
        self.set_status(status.DEFAULT_STATUS)

        v_layout = QtWidgets.QVBoxLayout()

        phase_name_widget = QtWidgets.QLabel(self._phase_name)
        phase_name_widget.setObjectName('h3')
        v_layout.addWidget(phase_name_widget)

        self._status_message_widget = QtWidgets.QLabel(self._status)
        self._status_message_widget.setObjectName('gray')
        v_layout.addWidget(self._status_message_widget)

        self.layout().addLayout(v_layout, 100)

        self._log_widget = QtWidgets.QFrame()
        self._log_widget.setVisible(False)
        self._log_widget.setLayout(QtWidgets.QVBoxLayout())
        self._log_widget.layout().addSpacing(10)

        self._log_text_edit = QtWidgets.QTextEdit()
        self._log_text_edit.setReadOnly(True)
        self._log_widget.layout().addWidget(self._log_text_edit, 10)
        self._close_button = QtWidgets.QPushButton('HIDE LOG')
        self._log_widget.layout().addWidget(self._close_button)
        self._log_overlay = OverlayWidget(self._log_widget)
        self._log_overlay.setVisible(False)

    def post_build(self):
        self.clicked.connect(self.show_log)
        self._close_button.clicked.connect(self._log_overlay.close)

    def update_status(self, new_status, status_message, log):
        '''Update the status of the phase to *new_status* and set *status_message*. 
        Build log messages from *log*.''' ''
        # Make sure widget not has been destroyed
        if shiboken2.isValid(self._status_message_widget):
            self._status_message_widget.setText(status_message)
        self.set_status(new_status)
        self.log = log

    def set_status(self, new_status):
        '''Visualize *new_status* on the button'''
        self._icon_widget.set_status(new_status)

    def show_log(self):
        self._log_overlay.setParent(self.parent())
        if len(self.log or '') > 0:
            self._log_text_edit.setText(self.log)
        else:
            self._log_text_edit.setText("No errors found")
        self._log_overlay.setVisible(True)
        self._log_widget.setVisible(True)
        self._log_overlay.resize(self.parent().size())


class StatusButtonWidget(QtWidgets.QPushButton):
    '''Progress status button representation, to be put inside the tool header.'''

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
        super(StatusButtonWidget, self).__init__(parent=parent)

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
