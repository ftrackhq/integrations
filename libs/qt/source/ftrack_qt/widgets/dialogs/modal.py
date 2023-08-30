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
        question=False,
        title=None,
        modal=True,
    ):
        '''
        Initialize a modal dialog either with a message/prompt, or as a base
        for a custom modal dialog.

        :param parent: The parent dialog or frame, required.
        :param message: The message or question to show in dialog, if not given it
        is assumed dialog will be further customised (f.e.x. the entity browser)
        :param question: If true, makes dialog behave like a prompt with Yes+No buttons
        :param title: The text to show in dialog title bar
        :param modal: The dialog should be modal, default is True
        '''
        super(ModalDialog, self).__init__(None, parent=parent)

        self.setParent(parent)

        self._message = message
        self._title = title or 'ftrack'
        self._question = question
        self._modal = modal

        self._approve_button = None
        self._deny_button = None

        self.pre_build()
        self.build()
        self.post_build()

        if modal is True:
            self.setModal(modal)
        self.setWindowFlags(
            QtCore.Qt.SplashScreen
            | (
                QtCore.Qt.WindowStaysOnTopHint
                if modal is True or message is not None
                else 0
            )
        )

    def __new__(
            cls, *args, **kwargs,
        ):
        ''' Override class instantiation to return exec_() if message is given'''
        instance = StyledDialog.__new__(cls, *args, **kwargs)
        if cls == ModalDialog:
            # Not inherited, so return exec_()
            instance.__init__(*args, **kwargs)
            return instance.exec_()
        else:
            return instance


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

        self.layout().addWidget(self.get_content_widget(), 100)

        buttonbar = QtWidgets.QWidget()
        buttonbar.setLayout(QtWidgets.QHBoxLayout())
        buttonbar.layout().setContentsMargins(10, 1, 10, 1)
        buttonbar.layout().setSpacing(10)

        buttonbar.layout().addWidget(QtWidgets.QLabel(), 100)
        self._approve_button = self.get_approve_button()
        if self._question:
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
        '''Create dialog main content widget, can be overridden to provide
        custom styled modal dialogs'''
        label = QtWidgets.QLabel(self._message)
        label.setObjectName('h3')
        return center_widget(label)

    def get_approve_button(self):
        '''Build the approve button widget'''
        button = QtWidgets.QPushButton(
            'YES' if self._question is True else 'OK'
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

        self.setWindowTitle(self._title or '')
        if self._message is not None:
            self.setMaximumHeight(100)
        self.resize(250, 100)


    def setWindowTitle(self, title):
        '''(Override) Set the dialog title'''
        super(ModalDialog, self).setWindowTitle(title)
        self._title_label.setText(title.upper())

    def setVisible(self, visible):
        '''(Override) Set visible'''
        if isinstance(self.parentWidget(), StyledDialog):
            self.parentWidget().darken = visible
        super(ModalDialog, self).setVisible(visible)
