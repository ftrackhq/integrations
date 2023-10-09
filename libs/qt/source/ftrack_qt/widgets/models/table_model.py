# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui


class TableModel(QtCore.QAbstractTableModel):
    '''Table model for generic data'''

    DATA_ROLE = QtCore.Qt.UserRole + 1

    @property
    def data_items(self):
        '''
        Returns the :obj:`data_items`
        '''
        return self._data_items

    @property
    def headers(self):
        '''
        Returns the :obj:`headers`
        '''
        return self._headers

    def __init__(self, column_mapping, parent=None):
        '''
        Initialise Model.
        *column_mapping*: is a dictionary to map data item keys to header titles
        '''
        super(TableModel, self).__init__(parent=parent)

        self._column_mapping = column_mapping
        self._headers = list(self._column_mapping.keys())
        self._data_items = []
        self._editable_columns = []

    def set_data_items(self, data_items):
        '''
        Reset the model and sets the :obj:`data_items` with the given
        *data_items*
        '''
        self.beginResetModel()
        self._data_items = data_items
        self.endResetModel()

    def set_editable_column(self, column_index):
        '''Sets the given *column_index* as editable'''
        if column_index not in self._editable_columns:
            self._editable_columns.append(column_index)

    def rowCount(self, parent):
        '''Return the row count for the internal data.'''
        if parent.column() > 0:
            return 0

        return len(self.data_items)

    def columnCount(self, parent):
        '''Return the column count for the internal data.'''
        return len(self._headers)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        '''Return the data provided in the given *index* and with *role*'''

        row = index.row()
        column = index.column()

        if not index.isValid():
            return None

        item = self.data_items[row]
        column_name = self._headers[column]

        # style versions
        if role == QtCore.Qt.TextAlignmentRole and column == 0:
            return QtCore.Qt.AlignCenter

        # style the rest
        elif role == QtCore.Qt.DisplayRole:
            if type(self._column_mapping[column_name]) == list:
                # Small function to get the value from recursive keys
                def get_recursive_keys(_item, keys):
                    if len(keys) == 1:
                        return _item[keys[0]]
                    return get_recursive_keys(_item[keys[0]], keys[1:])

                return get_recursive_keys(
                    item, self._column_mapping[column_name]
                )
            return str(item[self._column_mapping[column_name]])

        elif role == QtCore.Qt.EditRole:
            return item

        elif role == self.DATA_ROLE:
            return item

        return None

    def headerData(self, col, orientation, role):
        '''Provide header data'''
        if (
            orientation == QtCore.Qt.Horizontal
            and role == QtCore.Qt.DisplayRole
        ):
            return self._headers[col].capitalize()
        return None

    def flags(self, index):
        '''Set :obj:`self._editable_columns` editable'''
        if index.column() in self._editable_columns:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
