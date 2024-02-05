# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from Qt import QtGui, QtCore, QtWidgets


class StatusSelector(QtWidgets.QComboBox):
    '''A custom QComboBox for selecting statuses.'''

    statuses_changed = QtCore.Signal(object)

    @property
    def status(self):
        '''Return the currently selected status.'''
        index = self.currentIndex()
        if index > -1:
            return self.itemData(index)
        else:
            return None

    def __init__(self, parent=None):
        '''Initialize the StatusSelector.'''
        super(StatusSelector, self).__init__(parent=parent)

        self.setEditable(False)

        self.setMinimumWidth(150)
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)

    def set_statuses(self, statuses):
        '''Set the available statuses in the combo box.'''
        self.clear()
        for index, status in enumerate(statuses):
            self.addItem(status['name'].upper(), status)
            # TODO: color not working.
            color = QtGui.QColor(status['color'])
            self.setItemData(index, color, QtCore.Qt.ForegroundRole)
            self.setItemData(
                index, QtGui.QColor('#131920'), QtCore.Qt.BackgroundRole
            )
        self.setCurrentIndex(0)

    def set_status_by_name(self, name):
        '''Set the selected status by name.'''
        for index in range(self.count()):
            if self.itemData(index)['name'] == name:
                self.setCurrentIndex(index)
