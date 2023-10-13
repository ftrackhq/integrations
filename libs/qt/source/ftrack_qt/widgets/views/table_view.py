# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.models import TableModel


class TableView(QtWidgets.QTableView):
    '''Generic table view to represent an item.'''

    # This is to be re-implemented in the children
    selection_changed = QtCore.Signal(object)

    @property
    def table_model(self):
        return self._generic_model

    def __init__(self, column_mapping=None, parent=None):
        '''Initialise TableView with *column_mapping*

        *column_mapping*: Is a dictionary to map data item keys to header titles
        '''
        super(TableView, self).__init__(parent=parent)

        self._column_mapping = column_mapping
        self._generic_model = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''

        self.verticalHeader().hide()

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.horizontalHeader().setStretchLastSection(True)

    def build(self):
        '''Build widgets and parent them.'''
        self._generic_model = TableModel(
            column_mapping=self._column_mapping, parent=self
        )

        self.setModel(self._generic_model)

    def post_build(self):
        '''Perform post-construction operations.'''
        pass

    def set_data_items(self, data_items):
        '''
        Sets the :obj:`data_items` with the given *data_items*
        '''
        self.table_model.set_data_items(data_items)
