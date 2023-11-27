# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
# TODO: Clean this code
import urllib.request, urllib.parse, urllib.error

from Qt import QtCore, QtGui, QtWidgets

from ftrack_qt.widgets.thumbnails.open_base import OpenThumbnailBase


class OpenAssetVersionThumbnail(OpenThumbnailBase):
    '''Asset version thumbnail widget'''

    def _download(self, url):
        '''Return thumbnail from *reference*.'''
        url = url or self.placholderThumbnail
        return super(OpenAssetVersionThumbnail, self)._download(url)

    def get_thumbnail_url(self, component):
        if not component:
            return

        params = urllib.parse.urlencode(
            {
                'id': component['id'],
                'username': self.session.api_user,
                'apiKey': self.session.api_key,
            }
        )

        result_url = '{base_url}/component/thumbnail?{params}'.format(
            base_url=self.session._server_url, params=params
        )
        return result_url

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
