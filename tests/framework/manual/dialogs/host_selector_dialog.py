# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.dialogs import BaseDialog
from ftrack_qt.widgets.selectors import ListSelector


class HostSelectorDialog(BaseDialog):
    '''Default Framework Host Selector dialog'''

    name = 'framework_host_selector_dialog'
    tool_config_type_filter = []
    ui_type = 'qt'
    docked = False

    selected_host_changed = QtCore.Signal(object)
    refresh_hosts_clicked = QtCore.Signal()

    @property
    def host_connection_selector(self):
        return self._host_connection_selector

    @property
    def host_connections_ids(self):
        '''Returns available host id in the client'''
        ids = []
        for host_connection in self.host_connections:
            ids.append(host_connection.host_id)
        return ids

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
            self._host_connection_selector.set_current_item_index(0)
        if self.selected_host_connection_id != value:
            if not value:
                self._host_connection_selector.set_current_item_index(0)
                return
            self._host_connection_selector.set_current_item(value)

    def __init__(
        self,
        event_manager,
        client_id,
        connect_methods_callback,
        connect_setter_property_callback,
        connect_getter_property_callback,
        dialog_options,
        parent=None,
    ):
        '''
        Initialize Mixin class publisher dialog. It will load the qt dialog and
        mix it with the framework dialog.
        *event_manager*: instance of
        :class:`~ftrack_framework_core.event.EventManager`
        *client_id*: Id of the client that initializes the current dialog
        *connect_methods_callback*: Client callback method for the dialog to be
        able to execute client methods.
        *connect_setter_property_callback*: Client callback property setter for
        the dialog to be able to read client properties.
        *connect_getter_property_callback*: Client callback property getter for
        the dialog to be able to write client properties.
        *dialog_options*: Dictionary of arguments passed to configure the
        current dialog.
        '''
        self._host_connection_selector = None
        # As a mixing class we have to initialize the parents separately
        super(HostSelectorDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
        )

    def pre_build_ui(self):
        '''Pre Build method of the widget'''
        pass

    def build_ui(self):
        '''Build method of the widget'''
        self._host_connection_selector = ListSelector("Host Selector")
        self._tool_widget.layout().addWidget(self._host_connection_selector)

    def post_build_ui(self):
        '''Post Build method of the widget'''
        # Connect host selector signals
        self._host_connection_selector.current_item_changed.connect(
            self._on_host_selected_callback
        )
        self._host_connection_selector.refresh_clicked.connect(
            self._on_refresh_hosts_callback
        )

        # Add host connection items
        self.add_host_connection_items(self.host_connections_ids)
        if self.host_connection:
            # Prevent the sync calling on creation as host might be already set.
            self._on_client_host_changed_callback()

    def add_host_connection_items(self, host_connections_ids):
        '''Add given host_connections in the host_connection selector'''
        for host_connection_id in host_connections_ids:
            self._host_connection_selector.add_item(host_connection_id)

    def _on_host_selected_callback(self, host_connection_id):
        '''
        Emit signal with the new selected host_id and set the new
        host_connection to the client.
        '''
        if not host_connection_id:
            self.host_connection = None
            return

        for host_connection in self.host_connections:
            if host_connection.host_id == host_connection_id:
                self.host_connection = host_connection

        self.selected_host_changed.emit(self.selected_host_connection_id)

    def _on_refresh_hosts_callback(self):
        '''Clean up hast and emit signal to refresh host. Also ask client to re
        discover hosts.'''
        self.selected_host_changed.emit(None)
        self.refresh_hosts_clicked.emit()
        self.client_method_connection('discover_hosts')

    def _on_client_host_changed_callback(self, event=None):
        '''Client host has been changed'''
        client_host_connection_id = None
        if self.host_connection:
            client_host_connection_id = self.host_connection.host_id
        self.selected_host_connection_id = client_host_connection_id
