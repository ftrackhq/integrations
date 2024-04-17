# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

import ftrack_constants as constants
from ftrack_qt.utils.widget import set_property
from ftrack_qt.widgets.icons import StatusMaterialIconWidget
from ftrack_qt.widgets.overlay import OverlayWidget


class ProgressStatusButtonWidget(QtWidgets.QPushButton):
    '''Progress main status button representation, to be put inside the
    tool header.'''

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def __init__(self, parent=None):
        super(ProgressStatusButtonWidget, self).__init__(parent=parent)

        self._status = constants.status.UNKNOWN_STATUS

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
        self.setMinimumWidth(200)

    def build(self):
        self._message_label = QtWidgets.QLabel()
        self.layout().addWidget(self._message_label)
        self.layout().addStretch()
        self._status_icon = StatusMaterialIconWidget('')
        self.layout().addWidget(self._status_icon)

        self.set_status(constants.status.UNKNOWN_STATUS)

    def set_status(self, new_status, message=''):
        assert (
            new_status in constants.status.status_bool_mapping.keys()
        ), f'Invalid status: {new_status}'
        self.status = new_status
        if message:
            self._message_label.setText(message)
        set_property(self, 'status', self.status.lower())
        color = self._status_icon.set_status(self.status, size=24)
        self._message_label.setStyleSheet(f'color: #{color}')


class ProgressPhaseButtonWidget(QtWidgets.QPushButton):
    '''Showing progress of a progress phase, when pressed the log is shown.'''

    show_overlay_signal = QtCore.Signal(object)
    hide_overlay_signal = QtCore.Signal()

    @property
    def category(self):
        return self._category

    @property
    def label(self):
        return self._label

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def log_message(self):
        return self._log_message

    @log_message.setter
    def log_message(self, value):
        '''Store for log *value* for view and set it as tooltip'''
        self._log_message = value
        self.setToolTip(value or '')

    def __init__(self, label, category='', tags=None, parent=None):
        '''Instantiate the PhaseButtonWidget with *label* and *status*'''

        super(ProgressPhaseButtonWidget, self).__init__(parent=parent)

        self._label = label
        self._category = category
        self._tags = tags or []
        self._status = constants.status.UNKNOWN_STATUS
        self._log_message = None

        self._icon_widget = None
        self._status_message_widget = None
        self._log_message_widget = None
        self._log_text_edit = None
        self._time_widget = None
        self._overlay_widget = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.setMinimumHeight(
            48
        )  # Set minimum otherwise it will collapse the container
        self.setMinimumWidth(200)
        self.layout().setContentsMargins(3, 3, 3, 3)

    def build(self):
        self._icon_widget = StatusMaterialIconWidget(None)
        self.layout().addWidget(self._icon_widget)
        self.set_status(self.status)

        v_layout = QtWidgets.QVBoxLayout()

        label_widget = QtWidgets.QLabel(self._label)
        label_widget.setProperty('h3', True)
        v_layout.addWidget(label_widget)

        # Show tags as chips
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)

        for tag in self._tags:
            tag_widget = QtWidgets.QLabel(tag)
            tag_widget.setProperty('secondary', True)
            tag_widget.setStyleSheet(
                'background: #333333; padding: 1px; border-radius: 6px;'
            )
            h_layout.addWidget(tag_widget)
        h_layout.addWidget(QtWidgets.QLabel(''), 100)  # Add spacing

        v_layout.addLayout(h_layout)

        self.layout().addLayout(v_layout, 100)

        v_layout = QtWidgets.QVBoxLayout()

        self._status_message_widget = QtWidgets.QLabel(self.status)
        self._status_message_widget.setProperty('secondary', True)
        v_layout.addWidget(self._status_message_widget)

        self._time_widget = QtWidgets.QLabel()
        self._time_widget.setProperty('secondary', True)
        v_layout.addWidget(self._time_widget)

        self.layout().addLayout(v_layout)

        self._overlay_widget = OverlayWidget()

        self._log_message_widget = QtWidgets.QFrame()
        self._log_message_widget.setLayout(QtWidgets.QVBoxLayout())
        self._log_message_widget.layout().addSpacing(5)
        self._log_message_widget.layout().addWidget(
            QtWidgets.QLabel(f'{self.label} log:')
        )

        self._log_text_edit = QtWidgets.QTextEdit()
        self._log_text_edit.setReadOnly(True)
        self._log_message_widget.layout().addWidget(self._log_text_edit, 100)

        self._overlay_widget.set_widget(self._log_message_widget)

    def post_build(self):
        self.clicked.connect(self._on_click_callback)
        self._overlay_widget.close_button_clicked.connect(
            self._on_overlay_close_callback
        )

    def update_status(
        self, new_status, status_message, log_message, time=None
    ):
        '''Update the status of the phase to *new_status* and set *status_message*. 
        Build log messages from *log*.''' ''
        color = self.set_status(new_status)
        self._status_message_widget.setText(f'[{status_message.upper()}]')
        self._status_message_widget.setStyleSheet(f'color: #{color};')
        if time:
            self._time_widget.setText(f'{time:.3f}s')
        else:
            self._time_widget.setText('')
        self.log_message = log_message

    def set_status(self, new_status):
        '''Visualize *new_status* on the button'''
        self.status = new_status
        set_property(self, 'status', self.status.lower())
        return self._icon_widget.set_status(self.status)

    def _on_click_callback(self):
        '''Emits a show_overlay_signal when current widget is clicked'''
        self.show_overlay_signal.emit(self._overlay_widget)
        self.show_log()

    def _on_overlay_close_callback(self):
        '''Emits a hide_overlay_signal when overlay close button is clicked'''
        self.hide_overlay_signal.emit()

    def show_log(self):
        '''Sets the log message into the _log_text_edit'''
        if self.log_message:
            self._log_text_edit.setText(self.log_message)
        else:
            self._log_text_edit.setText("No errors found")
