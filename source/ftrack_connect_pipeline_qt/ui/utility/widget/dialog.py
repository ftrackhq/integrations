# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import platform

from functools import partial

from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.ui.utility.widget.button import (
    DenyButton,
    ApproveButton,
)
from ftrack_connect_pipeline_qt.utils import get_theme, set_theme
from ftrack_connect_pipeline_qt.utils import center_widget


class Dialog(QtWidgets.QDialog):
    '''
    A basic dialog window, intended to live on top of DCC app main window (assembler, change context, entity browser,..)
    Becomes shaded when a modal dialog is put in front of it.
    '''

    @property
    def darken(self):
        return self._darken

    @darken.setter
    def darken(self, value):
        self._darken = value
        if self._darken:
            self._overlay_widget = OverlayWidget(self)
            self._overlay_widget.move(0, 0)
            self._overlay_widget.resize(self.size())
            self._overlay_widget.show()
        else:
            if self._overlay_widget:
                self._overlay_widget.close()

    def __init__(self, parent):
        super(Dialog, self).__init__(parent=parent)
        self._overlay_widget = None


class OverlayWidget(QtWidgets.QWidget):
    '''The overlay widget used to shade the dialog'''

    def __init__(self, parent=None):
        super(OverlayWidget, self).__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._fill_color = QtGui.QColor(19, 25, 32, 169)

    def paintEvent(self, event):
        super(OverlayWidget, self).paintEvent(event)
        # Get current window size and paint a semi transparent dark overlay across widget
        size = self.size()
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(self._fill_color)
        painter.setBrush(self._fill_color)
        painter.drawRect(0, 0, size.width(), size.height())
        painter.end()


class ModalDialog(QtWidgets.QDialog):
    '''
    A styled modal ftrack dialog box/prompt, intended to live on top of a base dialog or DCC app and
    waits for user input by default
    '''

    def __init__(
        self,
        parent,
        message=None,
        question=None,
        title=None,
        modal=None,
    ):
        '''
        Initialize modal dialog

        :param parent: The parent dialog or frame
        :param message: The message to show in dialog, makes dialog on only have an OK button
        :param question: The question to show, makes dialog behave like a prompt with Yes+No buttons (default)
        :param title: The text to show in dialog title bar
        :param modal: The dialog should be modal
        '''
        super(ModalDialog, self).__init__(parent=parent)

        self.setParent(parent)

        self._message = message or question
        self._title = title or 'ftrack'
        self._dialog_mode = None

        self.setWindowFlags(QtCore.Qt.Tool)
        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        # None; A utility dialog not waiting for user input
        # True; A modal dialog waiting for user Yes or No input click
        # False; A modal dialog waiting for user OK input click
        if question:
            self._dialog_mode = True
        elif message:
            self._dialog_mode = False

        self.pre_build()
        self.build()
        self.post_build()

        if not modal is None:
            self.setModal(modal)
        self.setWindowFlags(
            QtCore.Qt.SplashScreen
            | (
                QtCore.Qt.WindowStaysOnTopHint
                if modal is True or (modal is None and message)
                else 0
            )
        )

        if self._dialog_mode is False:
            # Wait for confirmation
            self.exec_()

    def get_theme_background_style(self):
        return 'ftrack-modal'

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        '''Can be overridden by custom dialogs'''
        self._title_label = TitleLabel()
        self._title_label.setAlignment(QtCore.Qt.AlignCenter)
        self._title_label.setObjectName('titlebar')
        self.layout().addWidget(self._title_label)
        self._title_label.setMinimumHeight(24)

        self.layout().setSpacing(5)

        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())

        widget.layout().addWidget(self.get_content_widget())

        self.layout().addWidget(widget, 100)

        buttonbar = QtWidgets.QWidget()
        buttonbar.setLayout(QtWidgets.QHBoxLayout())
        buttonbar.layout().setContentsMargins(10, 1, 10, 1)
        buttonbar.layout().setSpacing(10)

        buttonbar.layout().addWidget(QtWidgets.QLabel(), 100)
        self._approve_button = self.get_approve_button()
        if not self._dialog_mode is False:
            self._deny_button = self.get_deny_button()
        else:
            self._deny_button = None
        if platform.system().lower() != 'darwin':
            if self._approve_button:
                buttonbar.layout().addWidget(self._approve_button)
            if self._deny_button:
                buttonbar.layout().addWidget(self._deny_button)
        else:
            if self._deny_button:
                buttonbar.layout().addWidget(self._deny_button)
            if self._approve_button:
                buttonbar.layout().addWidget(self._approve_button)

        self.layout().addWidget(buttonbar, 1)

    def get_content_widget(self):
        '''Create dialog main content widget, can be overridden by custom dialogs'''
        label = QtWidgets.QLabel(self._message)
        label.setObjectName('h3')
        return center_widget(label)

    def get_approve_button(self):
        '''Build the approve button widget'''
        return ApproveButton('YES' if self._dialog_mode is True else 'OK')

    def get_deny_button(self):
        '''Build the deny (No) button widget'''
        return DenyButton('NO')

    def post_build(self):
        if self._approve_button:
            self._approve_button.clicked.connect(partial(self.done, 1))
        if self._deny_button:
            self._deny_button.clicked.connect(self.reject)

        self.setWindowTitle(self._title)
        self.resize(250, 100)
        if not self._dialog_mode is None:
            self.setMaximumHeight(100)

    def setWindowTitle(self, title):
        '''(Override) Set the dialog title'''
        super(ModalDialog, self).setWindowTitle(title)
        self._title_label.setText(title.upper())

    def setVisible(self, visible):
        '''(Override) Set visible'''
        if isinstance(self.parentWidget(), Dialog):
            self.parentWidget().darken = visible
        super(ModalDialog, self).setVisible(visible)


class TitleLabel(QtWidgets.QLabel):
    def __init__(self, label="", parent=None):
        super(TitleLabel, self).__init__(label, parent=parent)
