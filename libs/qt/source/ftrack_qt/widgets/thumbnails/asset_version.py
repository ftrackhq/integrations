# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtCore, QtGui, QtWidgets

from ftrack_qt.widgets.thumbnails.base import ThumbnailBase


class AssetVersionThumbnail(ThumbnailBase):
    '''Asset version thumbnail widget'''

    def _download(self, url):
        '''Return thumbnail from *reference*.'''
        url = url or self.placholderThumbnail
        return super(AssetVersionThumbnail, self)._download(url)

    def _scaleAndSetPixmap(self, pixmap):
        '''Scale and set *pixmap*.'''
        if self._scale:
            scaled_pixmap = pixmap.scaled(
                self.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        else:
            scaled_pixmap = pixmap
        self.setPixmap(scaled_pixmap)
