# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import qtawesome as qta

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

from ftrack_connect.ui.widget.overlay import BlockingOverlay


class InstallerBlockingOverlay(BlockingOverlay):
    '''Custom blocking overlay for plugin installer.'''

    def __init__(
        self,
        parent,
        message='',
        icon=qta.icon('mdi6.check', color='#FFDD86', scale_factor=1.2),
    ):
        super(InstallerBlockingOverlay, self).__init__(
            parent,
            message=message,
            icon=icon,
        )

        self._text_edit = QtWidgets.QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFixedHeight(200)
        self.contentLayout.addWidget(self._text_edit)
        self._text_edit.setVisible(False)

        self._button_layout = QtWidgets.QHBoxLayout()
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.addSpacing(30)
        self.contentLayout.addLayout(self._button_layout)
        self.confirm_button = QtWidgets.QPushButton('Install more plugins')
        self.restart_button = QtWidgets.QPushButton('Restart')
        self.restart_button.setObjectName('primary')

        self._button_layout.addWidget(self.confirm_button)
        self._button_layout.addWidget(self.restart_button)
        self.confirm_button.hide()
        self.confirm_button.clicked.connect(self.hide)

    def set_reason(self, reason):
        self._text_edit.setText(reason)
        self._text_edit.setVisible(True)
