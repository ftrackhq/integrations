# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from Qt import QtWidgets, QtCore, QtSvg, QtGui
import shiboken2


class BusyIndicator(QtWidgets.QWidget):
    '''Widget implementing busy indicator - a spinning wheel'''

    def __init__(self, start=True, parent=None):
        '''Initialise indicator with optional *parent*.'''
        super(BusyIndicator, self).__init__(parent=parent)
        self._timer = None
        self._timerInterval = 30
        self._speed = 8.0
        self._spinnerAngle = 0
        # TODO: Use properties to enable setting this colour via stylesheets.
        self._spinnerColor = QtGui.QColor(100, 87, 53)  # Color: '#FFDD86'
        self._logo = ':ftrack/image/default/ftrackLogoColor'
        if start:
            self.start()

    def start(self):
        '''Start spinning if not already.'''
        if self._timer is None:
            self._timer = self.startTimer(self._timerInterval)
        if not self.isVisible():
            self.setVisible(True)

    def stop(self):
        '''Stop spinning if currently spinning.'''
        if shiboken2.isValid(self) and self._timer is not None:
            self.killTimer(self._timer)
            self._timer = None

    def timerEvent(self, event):
        '''Handle timer *event*.'''
        self._spinnerAngle += self._speed
        if self._spinnerAngle >= 360.0:
            self._spinnerAngle = 0.0

        self.repaint()

    def paintEvent(self, event):
        '''Paint widget.'''
        painter = QtGui.QPainter()
        painter.begin(self)

        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            area = QtCore.QRect(
                0, 0, painter.device().width(), painter.device().height()
            )
            center = QtCore.QPointF(area.width() / 2.0, area.height() / 2.0)

            # Draw in a normalised centered box.
            normalisedEdge = 100.0
            normalisedArea = QtCore.QRectF(
                -(normalisedEdge / 2.0),
                -(normalisedEdge / 2.0),
                normalisedEdge,
                normalisedEdge,
            )

            shortestSide = min(area.width(), area.height())
            painter.translate(center)
            painter.scale(
                shortestSide / normalisedEdge, shortestSide / normalisedEdge
            )

            # Draw spinner at current spin angle.
            pen = QtGui.QPen()
            penWidth = 8.0
            pen.setWidth(penWidth)
            pen.setColor(self._spinnerColor)
            pen.setCapStyle(QtCore.Qt.RoundCap)

            painter.setPen(pen)

            spinnerArea = QtCore.QRectF(
                normalisedArea.top() + (penWidth / 2.0),
                normalisedArea.left() + (penWidth / 2.0),
                normalisedArea.width() - penWidth,
                normalisedArea.height() - penWidth,
            )

            painter.drawArc(
                spinnerArea,
                -self._spinnerAngle * 16,  # Start angle.
                250 * 16,  # Span angle.
            )

        finally:
            painter.end()
