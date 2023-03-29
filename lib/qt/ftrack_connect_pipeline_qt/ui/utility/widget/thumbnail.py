# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import time
import os
import logging
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse

from Qt import QtCore, QtGui, QtWidgets
import shiboken2

from ftrack_connect_pipeline_qt.utils import BaseThread

# Cache of thumbnail images.
IMAGE_CACHE = dict()


class ThumbnailBase(QtWidgets.QLabel):
    '''Widget to load thumbnails from ftrack server.'''

    MAX_CONNECTIONS = 10  # Maximum number of parallel connections to allow

    thumbnailFetched = QtCore.Signal(object)
    thumbnailNotFound = QtCore.Signal()

    _connection_count = 0

    def __init__(self, session, scale=True, parent=None):
        super(ThumbnailBase, self).__init__(parent)
        self.session = session
        self._alive = True
        self._scale = scale

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # self._worker = None
        self.__loadingReference = None
        self.pre_build()
        self.post_build()

    def pre_build(self):
        self.thumbnailCache = {}
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.setAlignment(QtCore.Qt.AlignCenter)

        self.placholderThumbnail = (
            self.session.server_url + '/img/thumbnail2.png'
        )

    def post_build(self):
        self.thumbnailFetched.connect(self._downloaded)
        self.thumbnailNotFound.connect(self._use_placeholder)

    def load(self, reference):
        '''Load thumbnail from *reference* and display it.'''

        if reference in IMAGE_CACHE:
            if IMAGE_CACHE[reference] is not None:
                self._updatePixmapData(IMAGE_CACHE[reference])
            else:
                self._updateWithPlaceholderPixmap()
            return

        thread = BaseThread(
            name='get_thumbnail_thread',
            target=self._download_async,
            callback=self._downloaded_async,
            target_args=[reference],
        )
        thread.start()

        self.__loadingReference = reference

    def _download_async(self, reference):
        '''(Run in background thread) Download image'''
        while ThumbnailBase.MAX_CONNECTIONS <= ThumbnailBase._connection_count:
            time.sleep(0.01)
            # Thumbnail widget still active?
            if not shiboken2.isValid(self):
                return
        ThumbnailBase._connection_count += 1
        try:
            return self._download(reference)
        except urllib.error.URLError:
            # Not found
            if not shiboken2.isValid(self):
                # Thumbnail widget has been destroyed
                return
            self.thumbnailNotFound.emit()
        finally:
            ThumbnailBase._connection_count -= 1

    def _downloaded_async(self, html):
        '''(Run in background thread) Image has been downloaded, propagate to QT thread'''
        if not shiboken2.isValid(self):
            # Thumbnail widget has been destroyed
            return
        self.thumbnailFetched.emit(html)

    def _downloaded(self, result):
        '''Handler worker finished event.'''
        if not shiboken2.isValid(self):
            # Thumbnail widget has been destroyed
            return
        IMAGE_CACHE[self.__loadingReference] = result
        self._updatePixmapData(result)

        self.__loadingReference = None

    def _use_placeholder(self):
        '''Use placeholder image'''
        IMAGE_CACHE[self.__loadingReference] = None
        self._updateWithPlaceholderPixmap()

    def _updatePixmapData(self, data):
        '''Update thumbnail with *data*'''
        if data:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            self._scaleAndSetPixmap(pixmap)

    def _updateWithPlaceholderPixmap(self):
        '''Update thumbnail with default placeholder image'''
        resource_path = ':ftrack/image/default/placeholderThumbnail'
        self._scaleAndSetPixmap(QtGui.QPixmap(resource_path))

    def _scaleAndSetPixmap(self, pixmap):
        '''Scale and set *pixmap*.'''
        if self._scale:
            scaled_pixmap = pixmap.scaledToWidth(
                self.width(), mode=QtCore.Qt.SmoothTransformation
            )
        else:
            scaled_pixmap = pixmap
        self.setPixmap(scaled_pixmap)

    def _safeDownload(self, url, opener_callback, timeout=5):
        '''Check *url* through the given *openener_callback*.

        .. note::

           A placeholder image will be returned if there is not response within
           the given *timeout*.

        '''

        return opener_callback(url, timeout=timeout)

    def _download(self, url):
        '''Return thumbnail file from *url*.'''
        if url:
            ftrackProxy = os.getenv('FTRACK_PROXY', '')
            ftrackServer = self.session._server_url

            if ftrackProxy != '':
                if ftrackServer.startswith('https'):
                    httpHandle = 'https'
                else:
                    httpHandle = 'http'

                proxy = urllib.request.ProxyHandler({httpHandle: ftrackProxy})
                opener = urllib.request.build_opener(proxy)
                response = self._safeDownload(url, opener.open)
                html = response.read()
            else:
                response = self._safeDownload(url, urllib.request.urlopen)
                html = response.read()

            return html

        self.logger.warning('There is no url image to download')
        return None


class EllipseThumbnailBase(ThumbnailBase):
    '''Thumbnail which is drawn as an ellipse.'''

    def paintEvent(self, event):
        '''Override paint event to make round thumbnails.'''
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, True)

        brush = QtGui.QBrush(self.pixmap())

        painter.setBrush(brush)

        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 0)))

        painter.drawEllipse(QtCore.QRectF(0, 0, self.width(), self.height()))


class Context(ThumbnailBase):
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
            return super(Context, self)._download(url)
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


class AssetVersion(ThumbnailBase):
    '''Asset version thumbnail widget'''

    def _download(self, reference):
        '''Return thumbnail from *reference*.'''
        url = self.session.get('AssetVersion', reference)['thumbnail_url'][
            'url'
        ]
        url = url or self.placholderThumbnail
        return super(AssetVersion, self)._download(url)

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


class User(EllipseThumbnailBase):
    '''User(avatar) thumbnail widget'''

    def _download(self, reference):
        '''Return thumbnail from *reference*.'''
        thumbnail = self.session.query(
            'select thumbnail from User where username is "{}"'.format(
                reference
            )
        ).first()['thumbnail']
        url = self.get_thumbnail_url(thumbnail)
        return super(User, self)._download(url)

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
