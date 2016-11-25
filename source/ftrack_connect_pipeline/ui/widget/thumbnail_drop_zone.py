# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

from QtExt import QtWidgets, QtCore, QtGui


# Thumbnail limits from ftrack server.
THUMBNAIL_UPLOAD_MAX_SIZE = 10 * (1024 ** 2)  # 10 MiB in Bytes
THUMBNAIL_UPLOAD_VALID_FILE_TYPES = (
    'bmp', 'gif', 'jpeg', 'jpg', 'png', 'tif', 'tiff'
)


class ConnectThumbnailValidationError(Exception):
    '''ftrack thumbnail validation error.'''
    pass


class ThumbnailDropZone(QtWidgets.QWidget):
    '''Thumbnail widget with support for drag and drop and preview.'''

    updated = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Initialise widget.'''
        super(ThumbnailDropZone, self).__init__(*args, **kwargs)

        self.setObjectName('ftrack-connect-pipeline-thumbnail-drop-zone')

        layout = QtWidgets.QHBoxLayout()
        layout.addSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.setAcceptDrops(True)
        self.setProperty('ftrackDropZone', True)

        self._filePath = None
        self._imageWidth = 200
        self._imageHeight = 50

        self.thumbnail_button = QtWidgets.QPushButton('Import')
        self.setDropZoneText()
        layout.addWidget(self.thumbnail_button, 10)

        # TODO: Add theme support.
        removeIcon = QtGui.QIcon(
            QtGui.QPixmap(':/ftrack/image/light/trash')
        )
        self.removeButton = QtWidgets.QPushButton()
        self.removeButton.setVisible(False)
        self.removeButton.setFlat(True)
        self.removeButton.setIcon(removeIcon)
        self.removeButton.clicked.connect(self.removeThumbnail)

        layout.addWidget(self.removeButton, 0)
        self.thumbnail_button.clicked.connect(self.on_button_clicked)

    def on_button_clicked(self):
        '''Open file dialog with supported formats'''
        any_supported_format = 'Any ({0})'.format(' '.join(
            ['*.%s' % _format for _format in THUMBNAIL_UPLOAD_VALID_FILE_TYPES]
        ))

        supported_formats = ';;'.join(
            ['{0} Files (*.{1})'.format(_format.upper(), _format) for _format in THUMBNAIL_UPLOAD_VALID_FILE_TYPES]
        )

        format_filtering = any_supported_format + ';;' + supported_formats

        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Select Thumbnail', '/', format_filtering
        )

        if fname:
            self.setThumbnail(fname)

    def _getFilePathFromEvent(self, event):
        '''Get file path from *event*.

        Raises *ConnectThumbnailValidationError* if an invalid or unsupported
        file is added.

        '''
        # Validate single url
        if not event.mimeData().hasUrls():
            raise ConnectThumbnailValidationError('Invalid file.')

        urls = event.mimeData().urls()
        if len(urls) > 1:
            raise ConnectThumbnailValidationError(
                'Multiple files not supported.'
            )

        # Validate local file
        filePath = urls[0].toLocalFile()
        if not os.path.isfile(filePath):
            raise ConnectThumbnailValidationError('Invalid file.')

        # Validate file extension
        fileName, fileExtension = os.path.splitext(filePath)
        fileExtension = fileExtension[1:].lower()
        if fileExtension not in THUMBNAIL_UPLOAD_VALID_FILE_TYPES:
            raise ConnectThumbnailValidationError('Invalid file type.')

        # Validate file size
        fileSize = os.path.getsize(filePath)
        if fileSize > THUMBNAIL_UPLOAD_MAX_SIZE:
            raise ConnectThumbnailValidationError(
                'File size is above allowed maximum.'
            )

        return filePath

    def setThumbnail(self, filePath):
        '''Set thumbnail to *filePath* and display a preview.'''
        self._filePath = filePath
        pixmap = QtGui.QPixmap(self._filePath).scaled(
            self._imageWidth, self._imageHeight, QtCore.Qt.KeepAspectRatio
        )
        self.thumbnail_button.setIcon(pixmap)
        self.thumbnail_button.setIconSize(pixmap.rect().size())
        self.thumbnail_button.setText('')

        self.removeButton.setVisible(True)
        self.updated.emit(self._filePath)

    def setDropZoneText(self, text=None):
        '''Set and display drop zone label text as *text*.'''
        if not text:
            text = 'Drop a file here to add a thumbnail.'
        self.thumbnail_button.setText(text)

    def removeThumbnail(self):
        '''Remove thumbnail.'''
        self.setDropZoneText()
        self._filePath = None
        self.thumbnail_button.setIcon(QtGui.QPixmap())
        self.removeButton.setVisible(False)

    def _setDropZoneState(self, state='default'):
        '''Set drop zone state to *state*.

        *state* should be 'default', 'active' or 'invalid'.

        '''
        self.setProperty('ftrackDropZoneState', state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def dragEnterEvent(self, event):
        '''Validate file and set state when entering drop zone.'''
        try:
            self._getFilePathFromEvent(event)
            self._setDropZoneState('active')
            event.setDropAction(QtCore.Qt.CopyAction)
        except ConnectThumbnailValidationError:
            self._setDropZoneState('invalid')
            event.setDropAction(QtCore.Qt.IgnoreAction)
        event.accept()

    def dragLeaveEvent(self, event):
        '''Reset state when leaving drop zone.'''
        self._setDropZoneState()

    def _isThumbnailReplaceConfirmed(self):
        '''Confirm replacement if a thumbnail is set.'''
        if not self._filePath:
            return True

        response = QtWidgets.QMessageBox.question(
            self,
            'Replace thumbnail',
            'Do you want to replace the current thumbnail?',
            (
                QtWidgets.QMessageBox.StandardButton.Yes |
                QtWidgets.QMessageBox.StandardButton.No
            )
        )
        return (response == QtWidgets.QMessageBox.StandardButton.Yes)

    def dropEvent(self, event):
        '''Validate and set thumbnail when a file is droppped.'''
        self._setDropZoneState()
        try:
            filePath = self._getFilePathFromEvent(event)
            if self._isThumbnailReplaceConfirmed():
                self.setThumbnail(filePath)

        except ConnectThumbnailValidationError as error:
            QtWidgets.QMessageBox.warning(
                self, 'Invalid thumbnail', error.message
            )

    def getFilePath(self):
        '''Return image filePath for thumbnail.'''
        return self._filePath

    def clear(self):
        '''Remove thumbnail and reset initial state.'''
        self._filePath = None
        self.setDropZoneText()
