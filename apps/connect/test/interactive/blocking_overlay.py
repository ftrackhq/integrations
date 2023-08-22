# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtGui, QtCore, QtWidgets

import ftrack_connect.ui.widget.overlay
from harness import Harness


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''
        widget = QtWidgets.QFrame()
        widget.setFrameStyle(
            QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain
        )
        layout = QtWidgets.QVBoxLayout()
        widget.setLayout(layout)
        for index in range(5):
            label = QtWidgets.QLineEdit('Label {0}'.format(index))

            if index == 3:
                label.setDisabled(True)
                label.setText(label.text() + ' (Disabled)')

            layout.addWidget(label)

        textEdit = QtWidgets.QTextEdit('Text edit.')
        layout.addWidget(textEdit)

        button = QtWidgets.QPushButton('Push Button')
        button.setObjectName('primary')
        layout.addWidget(button)

        widget.overlay = ftrack_connect.ui.widget.overlay.BlockingOverlay(
            widget
        )

        widget.setMinimumSize(400, 400)

        return widget

    def constructController(self, widget):
        '''Return controller for *widget*.'''
        controlWidget = QtWidgets.QWidget()
        controlLayout = QtWidgets.QVBoxLayout()
        controlWidget.setLayout(controlLayout)

        layout = QtWidgets.QHBoxLayout()
        controlLayout.addLayout(layout)

        showButton = QtWidgets.QPushButton('Show')
        layout.addWidget(showButton)

        hideButton = QtWidgets.QPushButton('Hide')
        layout.addWidget(hideButton)

        showButton.clicked.connect(widget.overlay.show)
        hideButton.clicked.connect(widget.overlay.hide)

        messageEdit = QtWidgets.QLineEdit()
        messageEdit.setPlaceholderText('Enter message to display')
        controlLayout.addWidget(messageEdit)

        messageEdit.textChanged.connect(widget.overlay.setMessage)

        return controlWidget


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
