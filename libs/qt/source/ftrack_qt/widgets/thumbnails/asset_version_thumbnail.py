# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui

from ftrack_qt.widgets.thumbnails.base_thumbnail import ThumbnailBase


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
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        else:
            scaled_pixmap = pixmap
        self.setPixmap(scaled_pixmap)
