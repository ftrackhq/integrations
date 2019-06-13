# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import logging
import urllib
import urllib2

from qtpy import QtCore, QtGui, QtWidgets

from ftrack_connect_pipeline.utils import Worker

# Cache of thumbnail images.
IMAGE_CACHE = dict()


class Base(QtWidgets.QLabel):
    '''Widget to load thumbnails from ftrack server.'''

    def __init__(self, session, parent=None):
        super(Base, self).__init__(parent)
        self.session = session

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.thumbnailCache = {}
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.setAlignment(QtCore.Qt.AlignCenter)

        self.placholderThumbnail = (
            self.session._server_url + '/img/thumbnail2.png'
        )

        self._worker = None
        self.__loadingReference = None

    def load(self, reference):
        '''Load thumbnail from *reference* and display it.'''
        if reference in IMAGE_CACHE:
            self._updatePixmapData(IMAGE_CACHE[reference])
            return

        if self._worker and self._worker.isRunning():
            while self._worker:
                app = QtWidgets.QApplication.instance()
                app.processEvents()

        self._worker = Worker(
            self._download, [reference], parent=self
        )

        self.__loadingReference = reference
        self._worker.start()
        self._worker.finished.connect(self._workerFinnished)

    def _workerFinnished(self):
        '''Handler worker finished event.'''
        if self._worker:
            IMAGE_CACHE[self.__loadingReference] = self._worker.result
            self._updatePixmapData(self._worker.result)

        self._worker = None
        self.__loadingReference = None

    def _updatePixmapData(self, data):
        '''Update thumbnail with *data*.'''
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        self._scaleAndSetPixmap(pixmap)

    def _scaleAndSetPixmap(self, pixmap):
        '''Scale and set *pixmap*.'''
        scaledPixmap = pixmap.scaledToWidth(
            self.width(),
            mode=QtCore.Qt.SmoothTransformation
        )
        self.setPixmap(scaledPixmap)

    def _safeDownload(self, url, opener_callback, timeout=5):
        '''Check *url* through the given *openener_callback*.

        .. note::

           A placeholder image will be returned if there is not response within the
           given *timeout*.

        '''

        placeholder = self.placholderThumbnail
        try:
            response = opener_callback(url, timeout=timeout)
        except urllib2.URLError:
            response = opener_callback(placeholder)

        return response

    def _download(self, url):
        '''Return thumbnail file from *url*.'''
        ftrackProxy = os.getenv('FTRACK_PROXY', '')
        ftrackServer = self.session._server_url

        if ftrackProxy != '':
            if ftrackServer.startswith('https'):
                httpHandle = 'https'
            else:
                httpHandle = 'http'

            proxy = urllib2.ProxyHandler({httpHandle: ftrackProxy})
            opener = urllib2.build_opener(proxy)
            response = self._safeDownload(url, opener.open)
            html = response.read()
        else:
            response = self._safeDownload(url, urllib2.urlopen)
            html = response.read()

        return html


class EllipseBase(Base):
    '''Thumbnail which is drawn as an ellipse.'''

    def paintEvent(self, event):
        '''Override paint event to make round thumbnails.'''
        painter = QtGui.QPainter(self)
        painter.setRenderHints(
            QtGui.QPainter.Antialiasing,
            True
        )

        brush = QtGui.QBrush(
            self.pixmap()
        )

        painter.setBrush(brush)

        painter.setPen(
            QtGui.QPen(
                QtGui.QColor(0, 0, 0, 0)
            )
        )

        painter.drawEllipse(
            QtCore.QRectF(
                0, 0,
                self.width(), self.height()
            )
        )


class User(EllipseBase):

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

        params = urllib.urlencode({
            'id': component['id'],
            'username': self.session.api_user,
            'apiKey': self.session.api_key
        })

        result_url = '{base_url}/component/thumbnail?{params}'.format(
            base_url=self.session._server_url, params=params
        )
        return result_url
