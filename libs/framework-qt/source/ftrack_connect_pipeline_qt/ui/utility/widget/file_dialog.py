import os
from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline import utils as core_utils
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog


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


class ImageSequenceFileDialog(FileDialog):
    caption = 'Choose image sequence'

    def __init__(self, start_dir, dialog_filter, parent=None):
        '''
        Initialize File dialog
        '''
        super(ImageSequenceFileDialog, self).__init__(
            start_dir=start_dir, dialog_filter=dialog_filter, parent=parent
        )

    def proces_path(self, file_path):
        '''Process returned path of the file dialog'''
        file_path = os.path.normpath(file_path)

        image_sequence_path = core_utils.find_image_sequence(file_path)

        if not image_sequence_path:
            dialog.ModalDialog(
                None,
                title='Locate image sequence',
                message='An image sequence on the form "prefix.NNNN.ext" were not '
                'found at {}!'.format(file_path),
            )
        self._path = os.path.normpath(image_sequence_path)


class MovieFileDialog(FileDialog):
    caption = 'Choose Movie'
