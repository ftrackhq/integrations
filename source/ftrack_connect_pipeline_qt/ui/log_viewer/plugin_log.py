# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import json

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
    '''Main widget of the plugin log viewer'''

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
        '''Initialise LogViewerWidget with *event_manager* and *parent*

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

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

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

        self._search = Search(collapsed=False, collapsable=False)
        toolbar_layout.addWidget(self._search, 10)

        self.refresh_button = CircularButton('sync')
        toolbar_layout.addWidget(self.refresh_button)

        self.layout().addLayout(toolbar_layout)

        self.log_table_view = LogTableView(self.event_manager)

        self._scroll = scroll_area.ScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self.log_table_view)

        self.layout().addWidget(self._scroll, 100)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self._search.inputUpdated.connect(self._on_search)
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
        LogDetailDialog(self, data)


class LogTableView(QtWidgets.QTableView):
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
        '''Initialise LogTableView with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.
        '''
        super(LogTableView, self).__init__(parent=parent)

        self._event_manager = event_manager

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''

        self.setAlternatingRowColors(True)
        self.verticalHeader().hide()

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        header.setDefaultSectionSize(150)

    def build(self):
        '''Build widgets and parent them.'''
        self.log_model = LogTableModel(parent=self.parent())

        self.proxy_model = FilterProxyModel()
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


class LogDetailDialog(ModalDialog):
    TEMPLATE = """
        <div> <b>Date: </b>{date} </div> 
        <div> <b>Status: </b>{status} </div> 
        <div> <b>Host_id: </b>{host_id} </div> 
        <div> <b>Execution_time: </b>{execution_time} sec.</div> 
        <div> <b>Plugin_name: </b>{plugin_name} </div> 
        <div> <b>Plugin_type: </b>{plugin_type} </div>
    """

    def __init__(self, parent, data):
        self._data = data
        formatted_text = self.TEMPLATE.format(
            date=data.date,
            status=data.status,
            host_id=data.host_id,
            execution_time=data.execution_time,
            plugin_name=data.plugin_name,
            plugin_type=data.plugin_type,
            message=data.message or '',
            user_message=data.user_message or '',
        )

        super(LogDetailDialog, self).__init__(
            parent,
            title='View ftrack plugin log message',
            message=formatted_text,
            modal=True,
        )

    def get_content_widget(self):
        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())

        widget.layout().addWidget(
            super(LogDetailDialog, self).get_content_widget()
        )

        widget.layout().addWidget(QtWidgets.QLabel('Result:'))

        result_widget = QtWidgets.QTextEdit(
            json.dumps(self._data.result or {}, indent=2)
        )
        result_widget.setFontFamily('Courier New')
        result_widget.setReadOnly(True)
        result_widget.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        result_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        result_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        result_widget.setMinimumHeight(40)
        widget.layout().addWidget(result_widget, 100)

        widget.layout().addWidget(QtWidgets.QLabel('Message:'))

        message_widget = QtWidgets.QTextEdit(
            json.dumps(self._data.message or '', indent=2)
        )
        message_widget.setReadOnly(True)
        message_widget.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        message_widget.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn
        )
        message_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        message_widget.setMinimumHeight(40)
        widget.layout().addWidget(message_widget)

        widget.layout().addWidget(QtWidgets.QLabel('User message:'))

        user_message_widget = QtWidgets.QTextEdit(
            json.dumps(self._data.user_message + '', indent=2)
        )
        user_message_widget.setReadOnly(True)
        user_message_widget.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        user_message_widget.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn
        )
        user_message_widget.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn
        )
        user_message_widget.setMinimumHeight(40)
        widget.layout().addWidget(user_message_widget, 100)

        return widget
