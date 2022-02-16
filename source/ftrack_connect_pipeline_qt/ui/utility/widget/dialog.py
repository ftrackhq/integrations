import platform

from functools import partial

import qtawesome as qta

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt.utils import center_widget
from ftrack_connect_pipeline_qt.ui import theme


class Dialog(QtWidgets.QDialog):
    '''
    A styled ftrack dialog box, defaults to a prompt (Yes-No) dialog
    '''

    def __init__(self, question=None, title=None, parent=None):
        super(Dialog, self).__init__(parent=parent)

        self.setTheme(self.get_theme())
        self.setProperty('background', 'ftrack')

        self._question = question
        self._title = title or 'ftrack'

        self.pre_build()
        self.build()
        self.post_build()

    def get_theme(self):
        '''Return the client theme, return None to disable themes. Can be overridden by child.'''
        return 'dark'

    def setTheme(self, selected_theme):
        theme.applyFont()
        theme.applyTheme(self, selected_theme, 'plastique')

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)

    def build(self):
        ''' '''
        self.layout().addWidget(self.get_content_widget(), 100)

        buttonbar = QtWidgets.QWidget()
        buttonbar.setLayout(QtWidgets.QHBoxLayout())
        buttonbar.layout().setContentsMargins(10, 1, 10, 1)
        buttonbar.layout().setSpacing(10)

        buttonbar.layout().addWidget(QtWidgets.QLabel(), 100)
        self._approve_button = self.get_approve_button()
        self._deny_button = self.get_deny_button()

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
        return center_widget(QtWidgets.QLabel(self._question))

    def get_approve_button(self):
        return ApproveButton('YES')

    def get_deny_button(self):
        return DenyButton('NO')

    def post_build(self):
        if self._approve_button:
            self._approve_button.clicked.connect(partial(self.done, 1))
        if self._deny_button:
            self._deny_button.clicked.connect(self.reject)

        self.setWindowTitle(self.get_title())
        self.resize(250, 100)
        # self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        self.setModal(True)

    def get_title(self):
        return self._title


class DenyButton(QtWidgets.QPushButton):
    def __init__(self, label, width=40, height=35, parent=None):
        super(DenyButton, self).__init__(label, parent=parent)
        self.setMinimumSize(QtCore.QSize(width, height))


class ApproveButton(QtWidgets.QPushButton):
    def __init__(self, label, width=40, height=35, parent=None):
        super(ApproveButton, self).__init__(label, parent=parent)
        self.setMinimumSize(QtCore.QSize(width, height))
