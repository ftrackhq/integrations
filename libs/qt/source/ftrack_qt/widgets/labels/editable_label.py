# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore


class EditableLabel(QtWidgets.QLineEdit):
    '''Editable label widget.'''

    @property
    def previous_text(self):
        '''Return previous text.'''
        return self._previous_text

    @property
    def editable(self):
        '''Return editable state.'''
        return self._editable

    def __init__(self, text=None, editable=True, parent=None):
        super(EditableLabel, self).__init__(parent)
        self._previous_text = self.text()
        self._editable = editable
        self.setReadOnly(True)

        # Set the title line edit to be a label
        self.setProperty('label', True)
        self.setText(text or '')

        self.editingFinished.connect(self.on_editing_finished)

    def setText(self, event):
        super(EditableLabel, self).setText(event)

    def mouseDoubleClickEvent(self, event):
        if self._editable:
            if self.isReadOnly():
                self._previous_text = self.text()
                self.setReadOnly(False)
        super(EditableLabel, self).mouseDoubleClickEvent(event)

    def on_editing_finished(self):
        self.setReadOnly(True)
