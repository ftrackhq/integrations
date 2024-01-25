# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
# TODO: Clean this code

import urllib.request, urllib.parse, urllib.error

from Qt import QtCore, QtGui, QtWidgets

from ftrack_qt.widgets.thumbnails.session_base import SessionThumbnailBase


class ContextThumbnail(SessionThumbnailBase):
    '''Context thumbnail widget'''

    def _download(self, reference):
        '''Return thumbnail from *reference*.'''
        context = self.session.get('Context', reference)
        thumbnail = context['thumbnail']
        if thumbnail is None and context['thumbnail_id'] is not None:
            thumbnail = self.session.query(
                'FileComponent where id is "{}"'.format(
                    context['thumbnail_id']
                )
            ).one()
        url = self.get_thumbnail_url(thumbnail)
        if url is not None:
            return super(ContextThumbnail, self)._download(url)
        else:
            raise urllib.error.URLError("No context URL")

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
