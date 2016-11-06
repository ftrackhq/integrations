# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtCore, QtGui, QtWidgets, QtSvg


class BusyIndicator(QtWidgets.QWidget):
    '''Draw a busy indicator.'''

    def __init__(self, parent=None):
        '''Initialise indicator with optional *parent*.'''
        super(BusyIndicator, self).__init__(parent=parent)
        self._timer = None
        self._timerInterval = 30
        self._speed = 8.0
        self._spinnerAngle = 0
        # TODO: Use properties to enable setting this colour via stylesheets.
        self._spinnerColor = '#11b0e9'
        self._logo = ':ftrack/image/default/ftrackLogoColor'

        self.start()

    def start(self):
        '''Start spinning if not already.'''
        if self._timer is None:
            self._timer = self.startTimer(self._timerInterval)

    def stop(self):
        '''Stop spinning if currently spinning.'''
        if self._timer is not None:
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
            center = QtCore.QPointF(
                area.width() / 2.0,
                area.height() / 2.0
            )

            # Draw in a normalised centered box.
            normalisedEdge = 100.0
            normalisedArea = QtCore.QRectF(
                -(normalisedEdge / 2.0), -(normalisedEdge / 2.0),
                normalisedEdge, normalisedEdge
            )

            shortestSide = min(area.width(), area.height())
            painter.translate(center)
            painter.scale(
                shortestSide / normalisedEdge,
                shortestSide / normalisedEdge
            )

            # Draw logo.
            svgRenderer = QtSvg.QSvgRenderer()
            svgRenderer.load(self._logo)
            logoMargin = 30.0
            logoArea = normalisedArea.adjusted(
                logoMargin, logoMargin, -logoMargin, -logoMargin
            )
            svgRenderer.render(painter, logoArea)

            # Draw spinner at current spin angle.
            pen = QtGui.QPen()
            penWidth = 5.0
            pen.setWidth(penWidth)

            gradient = QtGui.QConicalGradient(
                QtCore.QPoint(0, 0),
                -self._spinnerAngle
            )
            gradient.setColorAt(0.95, QtCore.Qt.transparent)
            gradient.setColorAt(0, self._spinnerColor)

            brush = QtGui.QBrush(gradient)
            pen.setBrush(brush)
            painter.setPen(pen)

            spinnerArea = QtCore.QRectF(
                normalisedArea.top() + (penWidth / 2.0),
                normalisedArea.left() + (penWidth / 2.0),
                normalisedArea.width() - penWidth,
                normalisedArea.height() - penWidth
            )

            painter.drawArc(
                spinnerArea,
                0,  # Start angle.
                360 * 16  # Span angle.
            )

        finally:
            painter.end()
