# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore


class FileDialog(QtWidgets.QFileDialog):
    '''File dialog Widget'''

    caption = 'Choose file'

    @property
    def paths(self):
        '''Return selected path in the file dialog'''
        return self._paths

    def __init__(self, start_dir, dialog_filter, parent=None):
        '''
        Initialize File dialog
        '''
        super(FileDialog, self).__init__(parent=parent)
        self._paths = []
        (
            file_paths,
            unused_selected_filter,
        ) = self.getOpenFileNames(
            caption=self.caption, dir=start_dir, filter=dialog_filter
        )

        if not file_paths:
            return

        self.proces_path(file_paths)

    def proces_path(self, file_paths):
        '''Process returned path of the file dialog'''
        for path in file_paths:
            self._paths.append(os.path.normpath(path))
