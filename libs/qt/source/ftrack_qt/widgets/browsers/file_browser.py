# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from pathlib import Path
import clique

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_qt.widgets.dialogs import FileDialog
from ftrack_qt.widgets.dialogs import RadioButtonDialog


class FileBrowser(QtWidgets.QWidget):
    '''Browse Widget is a line edit with a browse button'''

    path_changed = QtCore.Signal(object)

    def __init__(self, parent=None):
        '''
        Initialize Browse widget
        '''
        super(FileBrowser, self).__init__(parent=parent)

        self._path_le = None
        self._browse_btn = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(15, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        '''Build widgets'''
        self._path_le = QtWidgets.QLineEdit()
        self._path_le.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.layout().addWidget(self._path_le, 20)

        self._browse_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_btn.setProperty('borderless', True)

        self.layout().addWidget(self._browse_btn)

    def post_build(self):
        '''Connect widget signals'''
        self._browse_btn.clicked.connect(self._browse_button_clicked)

    def get_path(self):
        '''Get path from the line edit'''
        return self._path_le.text()

    def set_path(self, path_text):
        '''Set path to the line edit'''
        self._path_le.setText(path_text)

    def set_tool_tip(self, tooltip_text):
        '''Set tooltip'''
        self._path_le.setToolTip(tooltip_text)

    def _browse_button_clicked(self):
        '''Browse button clicked signal'''
        start_dir = self._path_le.text() or Path.home()
        file_dialog = FileDialog(start_dir=str(start_dir), dialog_filter="*")
        selected_path = None
        if len(file_dialog.paths) > 1:
            selected_path = self.process_files_with_clique(file_dialog.paths)
        else:
            selected_path = file_dialog.paths[0]
        self.set_path(selected_path)
        self.path_changed.emit(selected_path)

    def process_files_with_clique(self, file_paths):
        '''Process the selected files with the clique library'''
        collections, remainder = clique.assemble(file_paths)
        collections_list = [collection.format() for collection in collections]
        collections_list.extend(remainder)
        if len(collections_list) > 1:
            radio_button_dialog = RadioButtonDialog(collections_list)
            if radio_button_dialog.exec_():
                selected_item = radio_button_dialog.selected_item()
                return selected_item
            else:
                return None
        else:
            return collections_list[0]
