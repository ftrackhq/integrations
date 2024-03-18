# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
# TODO: Clean this code

try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui

from ftrack_qt.widgets.thumbnails.session_base_thumbnail import (
    SessionThumbnailBase,
)


class EllipseThumbnailBase(SessionThumbnailBase):
    '''Thumbnail which is drawn as an ellipse.'''

    def paintEvent(self, event):
        '''Override paint event to make round thumbnails.'''
        painter = QtGui.QPainter(self)
        painter.setRenderHints(
            QtGui.QPainter.RenderHint.Antialiasing,
            True,
        )

        # TODO: when no image this raises an error because of the assigning of
        #  the empty pixmap. Find another way to solve this.
        brush = QtGui.QBrush(self.pixmap())

        painter.setBrush(brush)

        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 0)))

        painter.drawEllipse(QtCore.QRectF(0, 0, self.width(), self.height()))
