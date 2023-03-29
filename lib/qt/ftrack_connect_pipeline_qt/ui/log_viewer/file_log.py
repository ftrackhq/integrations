# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os
import sys
import subprocess
import traceback
import logging

from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline.configure_logging import get_log_directory
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)


class FileLogViewerWidget(QtWidgets.QWidget):
    '''Main widget of the file log viewer'''

    def __init__(self, parent=None):
        '''Initialise FileLogViewerWidget with *parent*'''
        super(FileLogViewerWidget, self).__init__(parent=parent)

        self.logger = logging.getLogger(__name__)

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(2, 2, 2, 2)
        self.layout().setSpacing(8)

    def build(self):
        '''Build widgets and parent them.'''
        toolbar_layout = QtWidgets.QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(5)

        self._files_combobox = FileSelector()
        toolbar_layout.addWidget(self._files_combobox, 10)

        self.refresh_button = CircularButton('sync')
        toolbar_layout.addWidget(self.refresh_button)

        self.layout().addLayout(toolbar_layout)

        self._content_textarea = QtWidgets.QTextEdit()
        self._content_textarea.setFontFamily('Courier New')
        self._content_textarea.setReadOnly(True)
        self._content_textarea.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self._content_textarea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn
        )
        self._content_textarea.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn
        )

        self.layout().addWidget(self._content_textarea, 100)

        self.open_log_folder_button = QtWidgets.QPushButton(
            'Open log directory'
        )

        self.layout().addWidget(self.open_log_folder_button)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.refresh_button.clicked.connect(self.refresh_ui)
        self.open_log_folder_button.clicked.connect(
            self._on_logging_button_clicked
        )
        self._files_combobox.currentIndexChanged.connect(
            self._on_file_index_changed
        )

    def refresh_ui(self):
        '''Find all log files in log directory'''

        cur_viewed_file = self._files_combobox.currentText()

        self._files_combobox.model().clear()

        log_directory_path = get_log_directory()

        if os.path.exists(log_directory_path):
            try:
                files = []
                for filename in os.listdir(log_directory_path):
                    files.append(
                        (
                            filename,
                            os.path.getmtime(
                                os.path.join(log_directory_path, filename)
                            ),
                        )
                    )
                selected_index = 0
                for index, (filename, unused_mtime) in enumerate(
                    sorted(files, key=lambda t: t[1], reverse=True)
                ):
                    self._files_combobox.addItem(filename)
                    if filename == cur_viewed_file:
                        selected_index = index
                if selected_index > -1:
                    self._files_combobox.setCurrentIndex(selected_index)
            except:
                self._content_textarea.setText(traceback.format_exc())
        else:
            self._content_textarea.setText(
                'Connect log directory "{}" does not exist!'.format(
                    log_directory_path
                )
            )

    def _on_file_index_changed(self, selected_index):
        '''Callback on user log file selection'''
        if len(self._files_combobox.currentText() or '') > 0:
            file_path = os.path.join(
                get_log_directory(), self._files_combobox.currentText()
            )
            self._content_textarea.clear()
            self.logger.info('Loading log file: "{}"'.format(file_path))
            with open(file_path, "r") as f:
                self._content_textarea.append(f.read())
        # self._content_textarea.append(" ") # Make sure last line is displayed

    def _open_directory(self, path):
        '''Open a filesystem directory from *path* in the OS file browser.

        If *path* is a file, the parent directory will be opened. Depending on OS
        support the file will be pre-selected.

        .. note::

            This function does not support file sequence expressions. The path must
            be either an existing file or directory that is valid on the current
            platform.

        '''
        if os.path.isfile(path):
            directory = os.path.dirname(path)
        else:
            directory = path

        if sys.platform == 'win32':
            subprocess.Popen(['start', directory], shell=True)

        elif sys.platform == 'darwin':
            if os.path.isfile(path):
                # File exists and can be opened with a selection.
                subprocess.Popen(['open', '-R', path])

            else:
                subprocess.Popen(['open', directory])

        else:
            subprocess.Popen(['xdg-open', directory])

    def _on_logging_button_clicked(self):
        '''Handle logging button clicked.'''
        directory = get_log_directory()
        self._open_directory(directory)


class FileSelector(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(FileSelector, self).__init__(parent=parent)
