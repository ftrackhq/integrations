from QtExt import QtCore, QtGui


class LogItem(object):

    def __init__(self):
        self._status = None
        self._duration = None
        self._name = None
        self._record = None
        self._time = None

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = value

    @property
    def name(self):
        return self._instance

    @name.setter
    def name(self, value):
        self._instance = value

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, value):
        self._record = value

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = value


class FilterProxyModel(QtGui.QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(FilterProxyModel, self).__init__(parent=parent)

        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)

    def filterAcceptsRowItself(self, source_row, source_parent):
        return super(FilterProxyModel, self).filterAcceptsRow(
            source_row, source_parent
        )

    def filterAcceptsRow(self, source_row, source_parent):
        if self.filterAcceptsRowItself(source_row, source_parent):
            return True

        parent = source_parent
        while parent.isValid():
            if self.filterAcceptsRowItself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()

        if self.hasAcceptedChildren(source_row, source_parent):
            return True

        return False

    def lessThan(self, left, right):
        left_data = self.sourceModel().item(left)
        right_data = self.sourceModel().item(right)
        return left_data.id > right_data.id


class LogTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, items):
        super(LogTableModel, self).__init__(parent)
        self._headers = ['status', 'time', 'duration', 'name', 'record']
        self._data = items

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._headers)

    def data(self, index, role):
        if not index.isValid():
            return None

        elif role != QtCore.Qt.DisplayRole:
            return None

        return getattr(self._data[index.row()], self._headers[index.column()])

    def headerData(self, col, orientation, role):
        if (
            orientation == QtCore.Qt.Horizontal and
            role == QtCore.Qt.DisplayRole
        ):
            return self._headers[col]
        return None
