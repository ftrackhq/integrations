# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
# TODO: Clean this code

from Qt import QtCore, QtGui, QtWidgets

from ftrack_qt.widgets.thumbnails.base import ThumbnailBase


class EllipseThumbnailBase(ThumbnailBase):
    '''Thumbnail which is drawn as an ellipse.'''

    def paintEvent(self, event):
        '''Override paint event to make round thumbnails.'''
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, True)

        # TODO: when no image this raises an error because of the assigning of
        #  the empty pixmap. Find another way to solve this.
        brush = QtGui.QBrush(self.pixmap())

        painter.setBrush(brush)

        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 0)))

        painter.drawEllipse(QtCore.QRectF(0, 0, self.width(), self.height()))
