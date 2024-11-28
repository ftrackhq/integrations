# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

import urllib
import urllib.error
import urllib.request

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import ftrack_connect.worker

# Cache of thumbnail images.
IMAGE_CACHE = dict()


class Base(QtWidgets.QLabel):
    '''Widget to load thumbnails from ftrack server.'''

    def __init__(self, parent=None):
        super(Base, self).__init__(parent)
        self.thumbnailCache = {}
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.placholderThumbnail = (
            os.environ['FTRACK_SERVER'] + '/img/thumbnail2.png'
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

        self._worker = ftrack_connect.worker.Worker(
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
            mode=QtCore.Qt.TransformationMode.SmoothTransformation,
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
        except urllib.error.URLError:
            response = opener_callback(placeholder)

        return response

    def _download(self, url):
        '''Return thumbnail file from *url*.'''

        ftrackProxy = os.getenv('FTRACK_PROXY', '')
        ftrackServer = os.getenv('FTRACK_SERVER', '')
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


class ActionIcon(Base):
    '''Widget to load action icons over HTTP.'''

    def __init__(self, parent=None, default_icon=None):
        '''Initialize action icon.'''
        super(ActionIcon, self).__init__(parent)
        self.setObjectName('action-icon')
        self.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
        self._default_icon = default_icon

    def setIcon(self, icon):
        '''Set *icon* to a supported icon or show the standard icon.

        *icon* may be one of the following.

            * A URL to load the image from starting with 'http'.
        '''
        if icon and isinstance(icon, QtGui.QIcon):
            super(ActionIcon, self).setPixmap(
                icon.pixmap(QtCore.QSize(self.width(), self.height()))
            )

        elif icon and icon[:4] == 'http':
            self.load(icon)
        else:
            super(ActionIcon, self).setPixmap(
                self._default_icon.pixmap(
                    QtCore.QSize(self.width(), self.height())
                )
            )

    def loadResource(self, resource):
        '''Update current pixmap using *resource*.'''
        pixmap = QtGui.QPixmap(QtCore.QSize(self.width(), self.height()))
        pixmap.load(resource)
        self._scaleAndSetPixmap(pixmap)

    def _scaleAndSetPixmap(self, pixmap):
        '''Scale *pixmap* to fit within current bounds'''
        scaledPixmap = pixmap.scaled(
            self.width(),
            self.height(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaledPixmap)
