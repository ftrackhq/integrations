# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore

    is_pyside6 = True
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

    is_pyside6 = False


class ShadedWidget(QtWidgets.QWidget):
    '''The overlay widget used to shade the dialog'''

    def __init__(self, parent=None):
        super(ShadedWidget, self).__init__(parent=parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            if is_pyside6
            else QtCore.Qt.FramelessWindowHint
        )
        self.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TranslucentBackground
            if is_pyside6
            else QtCore.Qt.WA_TranslucentBackground
        )
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
