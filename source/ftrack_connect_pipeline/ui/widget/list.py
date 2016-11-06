# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from QtExt import QtGui, QtCore, QtWidgets


class List(QtWidgets.QTableWidget):
    '''Manage a list of widgets.'''

    def __init__(self, parent=None):
        '''Initialise widget with *parent*.'''
        super(List, self).__init__(parent=parent)

        self._widgetColumn = 0

        self.setColumnCount(1)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.setVerticalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self.verticalHeader().hide()

        # Compatibility layer for PySide2/Qt5.
        # Please see: https://github.com/mottosso/Qt.py/issues/72
        # for more information.
        try:
            self.verticalHeader().setResizeMode(
                QtWidgets.QHeaderView.ResizeToContents
            )
        except Exception:
            self.verticalHeader().setSectionResizeMode(
                QtWidgets.QHeaderView.ResizeToContents
            )

        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().hide()

    def count(self):
        '''Return count of widgets in list.'''
        return self.rowCount()

    def addWidget(self, widget, row=None):
        '''Add *widget* to list at *row*.

        If *row* not specified then add to end of list.

        Return row item added at.

        '''
        if row is None:
            row = self.count()

        self.insertRow(row)
        self.setCellWidget(row, self._widgetColumn, widget)

        self.resizeRowToContents(row)

        return row

    def removeWidget(self, row):
        '''Remove and delete widget at *row*.'''
        self.removeCellWidget(row, self._widgetColumn)
        self.removeRow(row)

    def moveWidget(self, widget, newRow):
        '''Move a widget from it's old row to *newRow*.'''
        oldRow = self.indexOfWidget(widget)

        if oldRow:

            self.insertRow(newRow)

            # Collect the oldRow after insert to make sure we move the correct
            # widget.
            oldRow = self.indexOfWidget(widget)

            self.setCellWidget(newRow, self._widgetColumn, widget)
            self.resizeRowToContents(oldRow)

            # Remove the old row
            self.removeRow(oldRow)

    def clearWidgets(self):
        '''Remove all widgets.'''
        self.clear()
        self.setRowCount(0)

    def indexOfWidget(self, widget):
        '''Return row of *widget* in list or None if not present.'''
        index = None

        for row in range(self.count()):
            candidateWidget = self.widgetAt(row)
            if candidateWidget == widget:
                index = row
                break

        return index

    def widgets(self):
        '''Return list of widgets.'''
        widgets = []
        for row in range(self.count()):
            widget = self.widgetAt(row)
            widgets.append(widget)

        return widgets

    def widgetAt(self, row):
        '''Return widget at *row*.'''
        return self.cellWidget(row, self._widgetColumn)

    def selected(self):
        '''Return currently selected rows.'''
        selectionModel = self.selectionModel()
        indexes = selectionModel.selectedRows(self._widgetColumn)

        rows = []
        for index in indexes:
            rows.append(index.row())

        return rows
