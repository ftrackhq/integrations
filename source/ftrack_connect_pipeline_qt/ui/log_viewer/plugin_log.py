# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import os, sys, subprocess
from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline_qt.ui.log_viewer.model.log_table import (
    LogTableModel,
    FilterProxyModel,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import scroll_area
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import ModalDialog


class PluginLogViewerWidget(QtWidgets.QWidget):
    '''Main widget of the Log viewer'''

    TEMPLATE = """
    <div> <b>Status: </b>{status} </div> 
    <div> <b>Host_id: </b>{host_id} </div> 
    <div> <b>Widget_ref: </b>{widget_ref} </div> 
    <div> <b>Execution_time: </b>{execution_time} sec.</div> 
    <div> <b>Plugin_name: </b>{plugin_name} </div> 
    <div> <b>Plugin_type: </b>{plugin_type} </div>
    <p> <b>Result: </b>{result} </p>
    <p> <b>Message: </b>{message} </p>
    <p> <b>User Message: </b>{user_message} </p>
    """

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
        '''Returns results'''
        return self._results

    def __init__(self, event_manager, parent=None):
        '''Initialise LogViewerWidget with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.
        '''
        super(PluginLogViewerWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._results = []

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(2, 2, 2, 2)
        self.layout().setSpacing(8)

    def build(self):
        '''Build widgets and parent them.'''
        toolbar_layout = QtWidgets.QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        toolbar_layout.setSpacing(5)

        self._search = Search(
            collapsed=False, collapsable=False, parent=self.parent()
        )
        toolbar_layout.addWidget(self._search, 10)

        self.refresh_button = CircularButton('sync')
        toolbar_layout.addWidget(self.refresh_button)

        self.layout().addLayout(toolbar_layout)

        self.log_table_view = LogDialogTableView(
            self.event_manager, parent=self.parent()
        )

        self._scroll = scroll_area.ScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self.log_table_view)

        self.layout().addWidget(self._scroll, 100)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self._search.search.connect(self._on_search)
        self.log_table_view.doubleClicked.connect(self.show_detail_widget)

    def _on_search(self, value):
        '''Search in the current model.'''
        self.log_table_view.model().setFilterWildcard(value)

    def set_log_items(self, log_items):
        '''
        Sets the :obj:`log_items` with the given *log_items*
        '''
        self.log_table_view.set_log_items(log_items)

    def show_detail_widget(self, index):
        '''
        Raises a dock widget with the log details.
        '''

        data = self.log_table_view.model().data(
            index, self.log_table_view.model().DATA_ROLE
        )

        formated_text = self.TEMPLATE.format(
            status=data.status,
            host_id=data.host_id,
            widget_ref=data.widget_ref,
            execution_time=data.execution_time,
            plugin_name=data.plugin_name,
            plugin_type=data.plugin_type,
            result=data.result,
            message=data.message,
            user_message=data.user_message,
        )

        ModalDialog(
            self.parent(),
            title='View ftrack plugin log message',
            message=formated_text,
        )


class LogDialogTableView(QtWidgets.QTableView):
    '''Table view representing Log Viewer.'''

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def __init__(self, event_manager, parent=None):
        '''Initialise LogDialogTableView with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
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

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.horizontalHeader().setStretchLastSection(True)

    def build(self):
        '''Build widgets and parent them.'''
        self.log_model = LogTableModel(parent=self.parent())

        self.proxy_model = FilterProxyModel(parent=self.parent())
        self.proxy_model.setSourceModel(self.log_model)

        self.setModel(self.proxy_model)

    def post_build(self):
        '''Perform post-construction operations.'''
        pass

    def set_log_items(self, log_items):
        '''
        Sets the :obj:`log_items` with the given *log_items*
        '''
        self.log_model.set_log_items(log_items)


class LogViewerDetailWidget(QtWidgets.QDockWidget):
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
        super(LogViewerDetailWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._results = []

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        pass

    def build(self):
        self.textEdit = QtWidgets.QTextEdit()
        self.textEdit.setReadOnly(True)

        self.setWidget(self.textEdit)

    def post_build(self):
        pass

    def set_data(self, data):
        formated_text = self.template.format(
            status=data.status,
            host_id=data.host_id,
            widget_ref=data.widget_ref,
            execution_time=data.execution_time,
            plugin_name=data.plugin_name,
            plugin_type=data.plugin_type,
            result=data.result,
            message=data.message,
            user_message=data.user_message,
        )
        self.textEdit.setText(formated_text)
