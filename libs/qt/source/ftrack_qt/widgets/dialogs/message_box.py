# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui


class MessageBoxDialog(QtWidgets.QMessageBox):
    '''
    QMessageBoxDialog standarized for ftrack.
    '''

    @property
    def result(self):
        return self._result

    def __init__(
        self, title, message, button_1_text, button_2_text, parent=None
    ):
        super(MessageBoxDialog, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.setText(message)
        self.setIcon(QtWidgets.QMessageBox.Question)
        self.addButton(button_1_text, QtWidgets.QMessageBox.YesRole)
        self.addButton(button_2_text, QtWidgets.QMessageBox.NoRole)
        self._result = self.exec_()
