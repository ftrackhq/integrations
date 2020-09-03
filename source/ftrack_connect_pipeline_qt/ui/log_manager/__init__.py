# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os, sys, subprocess
from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline_qt.ui.log_manager.model.log_table import (
    LogTableModel, FilterProxyModel
)


class LogManagerWidget(QtWidgets.QWidget):

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    @property
    def results(self):
        '''Returns Session'''
        return self._results

    def __init__(self, event_manager, parent=None):
        super(LogManagerWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._results = []

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self._main_v_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._main_v_layout)

    def build(self):
        filter_layout = QtWidgets.QHBoxLayout()
        filter_label = QtWidgets.QLabel('Filter Log')
        self.filter_field = QtWidgets.QLineEdit()
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_field)
        self.layout().addLayout(filter_layout)

        self.log_table_view = LogDialogTableView(
            self.event_manager, parent=self
        )
        self.layout().addWidget(self.log_table_view)

    def post_build(self):
        self.filter_field.textChanged.connect(self.on_search)

    def on_search(self):
        '''Search in the current model.'''
        value = self.filter_field.text()
        self.log_table_view.model().setFilterWildcard(value)

    def set_log_items(self, log_items):
        '''
        Sets the ftrack_asset_list with the given *ftrack_asset_list*
        '''
        self.log_table_view.set_log_items(log_items)


class LogDialogTableView(QtWidgets.QTableView):
    '''Model representing AssetManager.'''

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def __init__(self, event_manager, parent=None):
        '''Initialise AssetManagerTableView with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''
        super(LogDialogTableView, self).__init__(parent=parent)

        self._event_manager = event_manager

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setAlternatingRowColors(True)
        self.verticalHeader().hide()

        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )

        QtCompat.setSectionResizeMode(
            self.verticalHeader(),
            QtWidgets.QHeaderView.ResizeToContents
        )

        self.horizontalHeader().setStretchLastSection(True)

    def build(self):
        '''Build widgets and parent them.'''
        self.log_model = LogTableModel(parent=self)

        self.proxy_model = FilterProxyModel(parent=self)
        self.proxy_model.setSourceModel(self.log_model)

        self.setModel(self.proxy_model)


    def post_build(self):
        '''Perform post-construction operations.'''
        pass

    def set_log_items(self, log_items):
        '''
        Sets the ftrack_asset_list with the given *ftrack_asset_list*
        '''
        self.log_model.set_log_items(log_items)