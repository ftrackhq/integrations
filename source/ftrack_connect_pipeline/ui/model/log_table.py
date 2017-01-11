# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtCore, QtGui, QtWidgets


class LogItem(object):
    '''Represents a Logging Item'''

    def __init__(self):
        '''LogItem initialization'''
        self._duration = None
        self.status = None
        self.name = None
        self.record = None
        self.time = None
        self.method = None

    @property
    def id(self):
        '''Return a unique identifier of the log entry.'''
        return '{0}.{1}.{2}'.format(
            self._name, self._method, self.time
        )

    @property
    def duration(self):
        '''Return the duration of the log entry.'''
        return round(self._duration, 4)

    @duration.setter
    def duration(self, value):
        '''Set the duration of the log entry.'''
        self._duration = value


class FilterProxyModel(QtCore.QSortFilterProxyModel):

    def __init__(self, parent=None):
        '''Initialize the FilterProxyModel'''
        super(FilterProxyModel, self).__init__(parent=parent)

        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)

    def filterAcceptsRowItself(self, source_row, source_parent):
        '''Provide a way to filter internal values.'''
        return super(FilterProxyModel, self).filterAcceptsRow(
            source_row, source_parent
        )

    def filterAcceptsRow(self, source_row, source_parent):
        '''Override filterAcceptRow to filter to any entry.'''
        if self.filterAcceptsRowItself(source_row, source_parent):
            return True

        parent = source_parent
        while parent.isValid():
            if self.filterAcceptsRowItself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()

        return False

    def lessThan(self, left, right):
        '''Allow to sort the model.'''
        left_data = self.sourceModel().item(left)
        right_data = self.sourceModel().item(right)
        return left_data.id > right_data.id


class LogTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, items):
        '''Initialize model model with *items*.'''

        super(LogTableModel, self).__init__(parent)
        self._headers = [
            'status', 'time', 'duration', 'name', 'method', 'record'
        ]

        self._data = items

    def rowCount(self, parent):
        '''Return the row count for the internal data.'''
        return len(self._data)

    def columnCount(self, parent):
        '''Return the column count for the internal data.'''
        return len(self._headers)

    def data(self, index, role):
        '''Return the data provided in the given *index* and with *role*'''

        row = index.row()
        column = index.column()

        if not index.isValid():
            return None

        elif role == QtCore.Qt.DisplayRole:
            return getattr(
                self._data[row],
                self._headers[column]
            )
        elif role == QtCore.Qt.TextAlignmentRole and column == 0:
            return QtCore.Qt.AlignCenter

    def headerData(self, col, orientation, role):
        '''Provide header data'''
        if (
            orientation == QtCore.Qt.Horizontal and
            role == QtCore.Qt.DisplayRole
        ):
            return self._headers[col].capitalize()
        return None
