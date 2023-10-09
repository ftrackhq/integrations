# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.headers import SessionHeader
from ftrack_qt.widgets.selectors import ContextSelector

from ftrack_qt.widgets.dialogs import StyledDialog


class TabDialog(StyledDialog):
    '''Base Class to represent a Plugin'''

    selected_context_changed = QtCore.Signal(object)
    selected_host_changed = QtCore.Signal(object)
    refresh_hosts_clicked = QtCore.Signal()
    selected_tab_changed = QtCore.Signal(object)

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
            pass
        if self.selected_host_connection_id != value:
            if not value:
                self._host_connection_selector.set_current_item_index(0)
                return
            self._host_connection_selector.set_current_item(value)

    def __init__(
        self,
        session,
        parent=None,
    ):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(TabDialog, self).__init__(parent=parent)

        self._session = session
        self._context_selector = None
        self._host_connection_selector = None
        self._tab_widget = None
        self._header = None

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

        self._tab_widget = QtWidgets.QTabWidget()

        self.layout().addWidget(self._header)
        self.layout().addWidget(self._context_selector, QtCore.Qt.AlignTop)
        self.layout().addWidget(self._host_connection_selector)
        self.layout().addWidget(self._tab_widget)

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
        # Connect tab widget
        self._tab_widget.currentChanged.connect(self._on_tab_changed_callback)

    def add_host_connection_items(self, host_connections_ids):
        '''Add given host_connections in the host_connection selector'''
        for host_connection_id in host_connections_ids:
            self._host_connection_selector.add_item(host_connection_id)

    def add_tab(self, tab_title, widget):
        self._tab_widget.addTab(widget, tab_title)

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

    def _on_tab_changed_callback(self, index):
        self.selected_tab_changed.emit(self._tab_widget.tabText(index))
