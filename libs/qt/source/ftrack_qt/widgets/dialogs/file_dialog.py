# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from Qt import QtWidgets, QtCore


class FileDialog(QtWidgets.QFileDialog):
    '''File dialog Widget'''

    caption = 'Choose file'

    @property
    def path(self):
        '''Return selected path in the file dialog'''
        return self._path

    def __init__(self, start_dir, dialog_filter, parent=None):
        '''
        Initialize File dialog
        '''
        super(FileDialog, self).__init__(parent=parent)
        self._path = None
        (
            file_path,
            unused_selected_filter,
        ) = self.getOpenFileName(
            caption=self.caption, dir=start_dir, filter=dialog_filter
        )

        if not file_path:
            return

        self.proces_path(file_path)

    def proces_path(self, file_path):
        '''Process returned path of the file dialog'''
        self._path = os.path.normpath(file_path)
