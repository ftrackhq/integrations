# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
# TODO: Clean this code
import time
import os
import logging
import urllib.request, urllib.parse, urllib.error

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    import shiboken6 as shiboken
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    import shiboken2 as shiboken

from ftrack_utils.threading import BaseThread

# Cache of thumbnail images.
IMAGE_CACHE = dict()


class SessionThumbnailBase(QtWidgets.QLabel):
    '''Widget to load thumbnails from ftrack server.'''

    MAX_CONNECTIONS = 10  # Maximum number of parallel connections to allow

    thumbnailFetched = QtCore.Signal(object)
    thumbnailNotFound = QtCore.Signal()

    _connection_count = 0

    def __init__(self, session, scale=True, parent=None):
        super(SessionThumbnailBase, self).__init__(parent)
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
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.placholderThumbnail = (
            self.session.server_url + '/img/thumbnail2.png'
        )

    def post_build(self):
        self.thumbnailFetched.connect(self._downloaded)
        self.thumbnailNotFound.connect(self.use_placeholder)

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
        while (
            SessionThumbnailBase.MAX_CONNECTIONS
            <= SessionThumbnailBase._connection_count
        ):
            time.sleep(0.01)
            # Thumbnail widget still active?
            if not shiboken.isValid(self):
                return
        SessionThumbnailBase._connection_count += 1
        try:
            return self._download(reference)
        except urllib.error.URLError:
            # Not found
            if not shiboken.isValid(self):
                # Thumbnail widget has been destroyed
                return
            self.thumbnailNotFound.emit()
        finally:
            SessionThumbnailBase._connection_count -= 1

    def _downloaded_async(self, html):
        '''(Run in background thread) Image has been downloaded, propagate to QT thread'''
        if not shiboken.isValid(self):
            # Thumbnail widget has been destroyed
            return
        self.thumbnailFetched.emit(html)

    def _downloaded(self, result):
        '''Handler worker finished event.'''
        if not shiboken.isValid(self):
            # Thumbnail widget has been destroyed
            return
        IMAGE_CACHE[self.__loadingReference] = result
        self._updatePixmapData(result)

        self.__loadingReference = None

    def use_placeholder(self):
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
                self.width(),
                mode=QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        else:
            scaled_pixmap = pixmap
        self.setPixmap(scaled_pixmap)

    def _safeDownload(self, url, opener_callback, timeout=5):
        '''Check *url* through the given *opener_callback*.

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
