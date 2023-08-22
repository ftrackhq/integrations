# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui


class ShadedWidget(QtWidgets.QWidget):
    '''The overlay widget used to shade the dialog'''

    def __init__(self, parent=None):
        super(ShadedWidget, self).__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._fill_color = QtGui.QColor(19, 25, 32, 169)

    def paintEvent(self, event):
        super(ShadedWidget, self).paintEvent(event)
        # Get current window size and paint a semi transparent dark overlay across widget
        size = self.size()
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(self._fill_color)
        painter.setBrush(self._fill_color)
        painter.drawRect(0, 0, size.width(), size.height())
        painter.end()
