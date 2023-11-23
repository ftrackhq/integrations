# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtGui, QtWidgets, QtCore

import ftrack_connect.ui.widget.overlay
from harness import Harness


class CustomOverlay(ftrack_connect.ui.widget.overlay.Overlay):
    '''Custom overlay for testing flexibility.'''

    def __init__(self, parent):
        '''Initialise.'''
        super(CustomOverlay, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        message = QtWidgets.QLabel('The background should be a pinkish color.')
        message.setWordWrap(True)
        message.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(message)

        self.setStyleSheet(
            '''
            QWidget#overlay {
                border: 5px solid black;
                background-color:rgba(255, 0, 0, 150);
            }

            QWidget#overlay QLabel {
                color: white;
                font-size: 16pt;
                background: transparent;
            }
        '''
        )


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''
        widget = QtWidgets.QFrame()
        widget.setFrameStyle(
            QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain
        )
        widget.setStyleSheet('QFrame { background-color: blue; }')

        self._overlay = CustomOverlay(widget)

        widget.setMinimumSize(400, 400)
        return widget


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
