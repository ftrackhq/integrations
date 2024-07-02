# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore


class EditableLabel(QtWidgets.QLineEdit):
    '''Editable label widget.'''

    forbidden_keys = ['a']

    @property
    def editable(self):
        '''Return editable state.'''
        return self._editable

    def __init__(self, text=None, editable=True, parent=None):
        super(EditableLabel, self).__init__(parent)
        self._editable = editable
        self.setReadOnly(True)

        # Set the title line edit to be a label
        self.setProperty('label', True)
        self.setText(text or '')

        self.editingFinished.connect(self.on_editing_finished)

    def mouseDoubleClickEvent(self, event):
        if self._editable:
            if self.isReadOnly():
                self.setReadOnly(False)

    def on_editing_finished(self):
        if self.forbidden_keys:
            for key in self.forbidden_keys:
                if key in self.text():
                    self.setText(self.text().replace(key, 'b'))
        self.setReadOnly(True)
