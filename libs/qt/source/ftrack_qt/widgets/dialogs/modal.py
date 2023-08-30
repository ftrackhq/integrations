# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import platform

from functools import partial

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.utils.widget import center_widget
from ftrack_qt.widgets.dialogs import StyledDialog


# TODO: Review and simplify this code
class ModalDialog(StyledDialog):
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
        super(ModalDialog, self).__init__(None, parent=parent)

        self.setParent(parent)

        self._message = message or question
        self._title = title or 'ftrack'
        self._dialog_mode = None

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
        self._title_label = QtWidgets.QLabel()
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
        button = QtWidgets.QPushButton(
            'YES' if self._dialog_mode is True else 'OK'
        )
        button.setMinimumSize(QtCore.QSize(40, 35))
        return button

    def get_deny_button(self):
        '''Build the deny (No) button widget'''
        button = QtWidgets.QPushButton('NO')
        button.setMinimumSize(QtCore.QSize(40, 35))
        return button

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
        if isinstance(self.parentWidget(), StyledDialog):
            self.parentWidget().darken = visible
        super(ModalDialog, self).setVisible(visible)
