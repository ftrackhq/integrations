# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtGui, QtWidgets, QtCore

import ftrack_connect.ui.widget.indicator
from harness import Harness


class WidgetHarness(Harness):
    '''Test harness for widget.'''

    def constructWidget(self):
        '''Return widget instance to test.'''
        indicator = ftrack_connect.ui.widget.indicator.BusyIndicator()
        indicator.setMinimumSize(100, 100)

        return indicator

    def constructController(self, widget):
        '''Return controller for *widget*.'''
        controlWidget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        controlWidget.setLayout(layout)

        startButton = QtWidgets.QPushButton('Start')
        layout.addWidget(startButton)

        stopButton = QtWidgets.QPushButton('Stop')
        layout.addWidget(stopButton)

        startButton.clicked.connect(widget.start)
        stopButton.clicked.connect(widget.stop)

        return controlWidget


if __name__ == '__main__':
    raise SystemExit(WidgetHarness().run())
