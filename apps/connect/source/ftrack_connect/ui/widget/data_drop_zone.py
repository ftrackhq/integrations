# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import os

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

import qtawesome as qta

import clique

# TODO: replace riffle as it is not PySide6 compatible
import riffle.browser
from riffle.icon_factory import IconFactory, IconType


class CustomIconFactory(IconFactory):
    def icon(self, specification):
        '''Return appropriate icon for *specification*.
        *specification* should be either:
            * An instance of :py:class:`riffle.model.Item`
            * One of the defined icon types (:py:class:`IconType`)
        '''
        if isinstance(specification, riffle.model.Item):
            specification = self.type(specification)

        icon = None

        if specification == IconType.Computer:
            icon = qta.icon('ftrack.computer')

        elif specification == IconType.Mount:
            icon = qta.icon('ftrack.dns')

        elif specification == IconType.Directory:
            icon = qta.icon('ftrack.folder')

        elif specification == IconType.File:
            icon = qta.icon('ftrack.file')

        elif specification == IconType.Collection:
            icon = qta.icon('ftrack.content-copy')

        return icon


class CustomFilesystemBrowser(riffle.browser.FilesystemBrowser):
    def _construct(self):
        super(CustomFilesystemBrowser, self)._construct()
        self._upButton.setIcon(qta.icon('mdi.chevron-up'))


class DataDropZone(QtWidgets.QFrame):
    '''Data drop zone widget.'''

    dataSelected = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Initialise DataDropZone widget.'''
        super(DataDropZone, self).__init__(*args, **kwargs)

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.setAcceptDrops(True)
        self.setObjectName('ftrack-connect-publisher-browse-button')
        self.setProperty('ftrackDropZone', True)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        bottomCenterAlignment = (
            QtCore.Qt.AlignmentFlag.AlignBottom
            | QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        topCenterAlignment = (
            QtCore.Qt.AlignmentFlag.AlignTop
            | QtCore.Qt.AlignmentFlag.AlignHCenter
        )

        self._label = QtWidgets.QLabel('Drop files here or')
        layout.addWidget(self._label, alignment=bottomCenterAlignment)

        self._browseButton = QtWidgets.QPushButton('BROWSE')
        self._browseButton.setToolTip('Browse for file(s).')
        layout.addWidget(self._browseButton, alignment=topCenterAlignment)

        self._setupConnections()

        homeFolder = os.path.expanduser('~')
        if os.path.isdir(homeFolder):
            self._currentLocation = homeFolder

    def _setupConnections(self):
        '''Setup connections to signals.'''
        self._browseButton.clicked.connect(self._browse)

    def _browse(self):
        '''Show browse dialog and emit dataSelected signal on file select.'''
        # Recreate browser on each browse to avoid issues where files are
        # removed and also get rid of any caching issues.
        dialog = CustomFilesystemBrowser(
            parent=self, iconFactory=CustomIconFactory()
        )
        dialog.setMinimumSize(900, 500)

        if self._currentLocation:
            dialog.setLocation(self._currentLocation)

        if dialog.exec_():
            selected = dialog.selected()
            if selected:
                item = selected[0]
                # Convert to unicode.
                if isinstance(item, str):
                    item = item
                self.dataSelected.emit(item)

        # TODO: This is fragile and should probably be available as public
        # reload method in the Riffle project.
        self._currentLocation = dialog._locationWidget.itemData(
            dialog._locationWidget.currentIndex()
        )

        dialog.destroy()

    def _setDropZoneState(self, state='default'):
        '''Set drop zone state to *state*.

        *state* should be 'default', 'active' or 'invalid'.

        '''
        self.setProperty('ftrackDropZoneState', state)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _processMimeData(self, mimeData, raise_message=True):
        '''Return a list of valid filepaths.'''
        validPaths = []

        if not mimeData.hasUrls():
            QtWidgets.QMessageBox.warning(
                self,
                'Invalid file',
                'Invalid file: the dropped item is not a valid file.',
            )
            return validPaths

        for path in mimeData.urls():
            localPath = path.toLocalFile()
            if os.path.isfile(localPath):
                validPaths.append(localPath)
                self.log.debug(u'Dropped file: {0}'.format(localPath))
            else:
                self._setDropZoneState('invalid')

                if raise_message:
                    message = (
                        u'Invalid file: "{0}" is not a valid file.'.format(
                            localPath
                        )
                    )
                    if os.path.isdir(localPath):
                        message = (
                            'Folders not supported.\n\nIn the current version, '
                            'folders are not supported. This will be enabled in a '
                            'later release of ftrack connect.'
                        )

                    QtWidgets.QMessageBox.warning(
                        self, 'Invalid file', message
                    )

                    self._setDropZoneState()

        return validPaths

    def clear(self):
        '''Clear the browser to it's initial state.'''
        # Since the dialog is re-created when opened, we don't need to clear it.
        pass

    def dragEnterEvent(self, event):
        '''Override dragEnterEvent and accept all events.'''
        event.setDropAction(QtCore.Qt.DropAction.CopyAction)
        event.accept()
        files = self._processMimeData(event.mimeData(), raise_message=False)
        if files:
            self._setDropZoneState('active')

    def dragLeaveEvent(self, event):
        '''Override dragLeaveEvent and accept all events.'''
        event.accept()
        self._setDropZoneState()

    def dropEvent(self, event):
        '''Handle dropped file event.'''
        self._setDropZoneState()

        # TODO: Allow hook into the dropEvent.

        paths = self._processMimeData(event.mimeData())

        self.log.debug(u'Paths: {0}'.format(paths))

        # Use frames pattern instead of default digits pattern to only match
        # frame sequences.
        framesPattern = clique.PATTERNS.get('frames')
        sequences, remainders = clique.assemble(
            paths, patterns=[framesPattern], assume_padded_when_ambiguous=True
        )

        self.log.debug(u'Sequences: {0}'.format(sequences))
        self.log.debug(u'Remainders: {0}'.format(remainders))

        for sequence in sequences:
            self.dataSelected.emit(sequence.format())

        for path in remainders:
            self.dataSelected.emit(path)

        event.accept()
