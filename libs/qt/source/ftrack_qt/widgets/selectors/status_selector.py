# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtGui, QtCore, QtWidgets


class StatusSelector(QtWidgets.QComboBox):
    statuses_changed = QtCore.Signal(object)

    @property
    def status(self):
        '''Return current selected asset version entity'''
        index = self.currentIndex()
        if index > -1:
            return self.itemData(index)
        else:
            return None

    def __init__(self, parent=None):
        super(StatusSelector, self).__init__(parent=parent)

        self.setEditable(False)

        self.setMinimumWidth(150)
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)

    def set_statuses(self, statuses):
        '''Set statuses on the combo box'''
        self.clear()
        for index, status in enumerate(statuses):
            self.addItem(status['name'].upper(), status)
            # TODO: color not working.
            color = QtGui.QColor(status['color'])
            self.setItemData(index, color, QtCore.Qt.ForegroundRole)
        self.setCurrentIndex(0)

    def set_status_by_name(self, name):
        for index in range(self.count()):
            if self.itemData(index)['name'] == name:
                self.setCurrentIndex(index)
