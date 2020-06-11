# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.constants import asset as asset_constants
from Qt import QtWidgets, QtCore


class AssetManagerModel(QtCore.QAbstractTableModel):
    '''Model representing AssetManager.'''

    #: Signal that a loading operation has started.
    # loadStarted = QtCore.Signal()
    #
    # #: Signal that a loading operation has ended.
    # loadEnded = QtCore.Signal()

    def __init__(self, ftrack_asset_list=None, parent=None):
        '''Initialise with *root* entity and optional *parent*.'''
        super(AssetManagerModel, self).__init__(parent=parent)
        self.ftrack_asset_list = ftrack_asset_list
        self.columns = self.ftrack_asset_list[0].asset_info.keys()

    def rowCount(self, parent=QtCore.QModelIndex()):
        '''Return number of children *parent* index has.

        *parent* QModelIndex
        '''
        # if parent.column() > 0:
        #     return 0
        #
        # if parent.isValid():
        #     item = parent.internalPointer()
        # else:
        #     item = self.ftrack_asset

        return len(self.ftrack_asset_list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        '''Return amount of data *parent* index has.'''
        return len(self.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < self.rowCount():
            return None
        if not index.isValid() or not 0 <= index.column() < self.columnCount():
            return None

        column = index.column()
        row = index.row()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self.ftrack_asset_list[row].asset_info[self.columns[column]]

        return None

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if section < len(self.columns):
                column = self.columns[section]
                if role == QtCore.Qt.DisplayRole:
                    return column

        return None

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        self.ftrack_asset_list[index.row()].set_asset_version(value)
        # if role == QtCore.Qt.EditRole:
        #     if value:
        #         self.ftrack_asset_list[index.row()].set_asset_version(value)
        #         #TODO: activate this signal is the signal to say that the data has changed
        #         #self.dataChanged.emit(index, index)
        #         return True
        #     return False

    def flags(self, index):
        #flag = super(AssetManagerModel, self).flags(index)
        if (index.column() == self.get_version_column_idx()):
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsEnabled

    def item(self, index):
        '''Return item at *index*.'''
        # self.data(index)#, role=self.ITEM_ROLE)
        return self.ftrack_asset_list[index.row()]

    def get_version_column_idx(self):
        return self.columns.index(asset_constants.VERSION_NUMBER)