# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.headers import SessionHeader
from ftrack_qt.widgets.selectors import ContextSelector

from ftrack_qt.widgets.dialogs import StyledDialog


class ScrollToolConfigsDialog(StyledDialog):
    '''Base Class to represent a Plugin'''

    selected_context_changed = QtCore.Signal(object)
    selected_host_changed = QtCore.Signal(object)
    selected_tool_config_changed = QtCore.Signal(object)
    refresh_hosts_clicked = QtCore.Signal()
    refresh_tool_configs_clicked = QtCore.Signal()
    run_button_clicked = QtCore.Signal()

    @property
    def tool_config_widget(self):
        '''Return the tool config widget of the dialog'''
        return self._tool_config_widget

    @property
    def run_button_title(self):
        '''Return the label of the run button'''
        return self._run_button_title

    @run_button_title.setter
    def run_button_title(self, value):
        '''Set the label of the run button'''
        self._run_button_title = str(value)

    @property
    def selected_context_id(self):
        '''Return the selected context id in the context sleector'''
        return self._context_selector.context_id

    @selected_context_id.setter
    def selected_context_id(self, value):
        '''Set the given *value* as the selected context id'''
        if self.selected_context_id != value:
            self._context_selector.context_id = value

    @property
    def is_browsing_context(self):
        '''
        Return if context selector is currently working on seting up a context
        '''
        return self._context_selector.is_browsing

    @property
    def selected_host_connection_id(self):
        '''Return the selected host connection id'''
        if self._host_connection_selector.current_item_index() in [0, -1]:
            return None
        return self._host_connection_selector.current_item_text()

    @selected_host_connection_id.setter
    def selected_host_connection_id(self, value):
        '''Set the given *value* as selected host_connection_id'''
        if not self.selected_host_connection_id and not value:
            self._tool_config_selector.clear_items()
            self.clear_tool_config_ui()
        if self.selected_host_connection_id != value:
            self._tool_config_selector.clear_items()
            self.clear_tool_config_ui()
            if not value:
                self._host_connection_selector.set_current_item_index(0)
                return
            self._host_connection_selector.set_current_item(value)

    @property
    def selected_tool_config_name(self):
        '''Return the selected tool config name'''
        if self._tool_config_selector.current_item_index() in [0, -1]:
            return None
        return self._tool_config_selector.current_item_text()

    @selected_tool_config_name.setter
    def selected_tool_config_name(self, value):
        '''Set the given *value* as the selected tool config name'''
        if not self.selected_tool_config_name and not value:
            self.clear_tool_config_ui()
        if self.selected_tool_config_name != value:
            self.clear_tool_config_ui()
            if not value:
                self._tool_config_selector.set_current_item_index(0)
                return
            self._tool_config_selector.set_current_item(value)

    def __init__(
        self,
        session,
        parent=None,
    ):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(ScrollToolConfigsDialog, self).__init__(parent=parent)

        self._session = session
        self._context_selector = None
        self._host_connection_selector = None
        self._tool_config_selector = None
        self._header = None
        self._scroll_area = None
        self._tool_config_widget = None
        self._run_button = None
        self._run_button_title = 'Run'

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        # Create the header
        self._header = SessionHeader(self._session)
        # TODO: implement progress widget.
        # self._progress_widget = ProgressWidget
        # self._header.add_widget(self._progress_widget)

        # TODO: we have to update the signals from the context selector to
        #  identify that are our signals and not qt signals. So make them snake case
        self._context_selector = ContextSelector(
            self._session, enble_context_change=True
        )

        self._host_connection_selector = ListSelector("Host Selector")

        self._tool_config_selector = ListSelector("Configs")

        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )

        self._tool_config_widget = QtWidgets.QWidget()
        _tool_config_widget_layout = QtWidgets.QVBoxLayout()
        self._tool_config_widget.setLayout(_tool_config_widget_layout)

        self._run_button = QtWidgets.QPushButton(self._run_button_title)

        self.layout().addWidget(self._header)
        self.layout().addWidget(self._context_selector, QtCore.Qt.AlignTop)
        self.layout().addWidget(self._host_connection_selector)
        self.layout().addWidget(self._tool_config_selector)
        self.layout().addWidget(self._scroll_area, 100)
        self._scroll_area.setWidget(self._tool_config_widget)
        self.layout().addWidget(self._run_button)

    def post_build(self):
        '''Set up all the signals'''
        # Connect context selector signals
        self._context_selector.context_changed.connect(
            self._on_context_selected_callback
        )
        # Connect host selector signals
        self._host_connection_selector.current_item_changed.connect(
            self._on_host_selected_callback
        )
        self._host_connection_selector.refresh_clicked.connect(
            self._on_refresh_hosts_callback
        )
        # Connect tool_config selector signals
        self._tool_config_selector.current_item_changed.connect(
            self._on_tool_config_selected_callback
        )
        self._tool_config_selector.refresh_clicked.connect(
            self._on_refresh_tool_configs_callback
        )
        # Connect run_tool_config button
        self._run_button.clicked.connect(self._on_run_button_clicked)

    def add_host_connection_items(self, host_connections_ids):
        '''Add given host_connections in the host_connection selector'''
        for host_connection_id in host_connections_ids:
            self._host_connection_selector.add_item(host_connection_id)

    def add_tool_config_items(self, tool_config_names):
        '''Add given tool_configs to tool config selector'''
        for tool_config_name in tool_config_names:
            self._tool_config_selector.add_item(tool_config_name)

    def _on_context_selected_callback(self, context_id):
        '''Emit signal with the new context_id'''
        if not context_id:
            return
        self.selected_context_changed.emit(context_id)

    def _on_host_selected_callback(self, item_text):
        '''
        Emit signal with the new selected host_id
        '''

        if not item_text:
            return
        self.selected_host_changed.emit(self.selected_host_connection_id)

    def _on_refresh_hosts_callback(self):
        '''Clean up hast and emit signal to refresh hosts'''
        self.selected_host_changed.emit(None)
        self.refresh_hosts_clicked.emit()

    def _on_tool_config_selected_callback(self, item_text):
        '''Emit signal with the new selected tool config'''
        if not item_text:
            return
        self.selected_tool_config_changed.emit(self.selected_tool_config_name)

    def _on_refresh_tool_configs_callback(self):
        '''Clean up tool_configs and emit signal to refresh them'''
        # TODO: double think if tool_configs can be refreshed? maybe we should
        #  thn re-select the same host instead of discovering hosts again?
        self.selected_tool_config_changed.emit(None)
        self.refresh_tool_configs_clicked.emit()

    def _on_run_button_clicked(self):
        '''Emit signal of run button.'''
        self.run_button_clicked.emit()

    def clear_tool_config_ui(self):
        '''Remove all widgets from the tool_config_widget layout'''
        for i in reversed(range(self._tool_config_widget.layout().count())):
            self._tool_config_widget.layout().itemAt(i).widget().deleteLater()
