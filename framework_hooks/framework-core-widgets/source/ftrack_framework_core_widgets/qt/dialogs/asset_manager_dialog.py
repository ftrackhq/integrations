# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

import ftrack_constants.framework.definition
from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.headers import SessionHeader
from ftrack_qt.widgets.selectors import DropdownSelector
from ftrack_qt.widgets.dialogs import StyledDialog, ModalDialog
from ftrack_qt.widgets.browsers import AssetManagerBrowser
from ftrack_qt.widgets.model import AssetInfoListModel


class AssetManagerDialog(FrameworkDialog, StyledDialog):
    '''Default Framework Asset Manager widget'''

    name = 'framework_asset_manager_dialog'
    definition_type_filter = ['asset_manager']
    ui_type = 'qt'
    docked = True

    selected_host_changed = QtCore.Signal(object)

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
            self._asset_list_model.reset()
        if self.selected_host_connection_id != value:
            self._asset_list_model.reset()
            if not value:
                self._host_connection_selector.set_current_item_index(0)
                return
            self._host_connection_selector.set_current_item(value)

    @property
    def definition_names(self):
        '''Returns available definition names in the client'''
        names = []
        for definitions in self.filtered_definitions:
            for definition in definitions:
                names.append(definition.name)
        return names

    @property
    def asset_manager_browser(self):
        '''Returns the current asset manager widget'''
        return self._asset_manager_browser

    @asset_manager_browser.setter
    def asset_manager_browser(self, value):
        '''
        Updates the current asset manager widget with the given *value*
        '''
        self._asset_manager_browser = value

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
        Initialize Mixin class asset manager dialog. It will load the qt dialog and
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
        # As a mixing class we have to initialize the parents separately
        StyledDialog.__init__(
            self,
            parent=parent,
        )
        FrameworkDialog.__init__(
            self,
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
        )
        self._asset_manager_browser = None
        self._asset_list_model = (dialog_options or {}).get('model')
        if self._asset_list_model is None:
            self.logger.warning(
                'No global asset list model provided, creating.'
            )
            self._asset_list_model = AssetInfoListModel()
        self._in_assembler = (dialog_options or {}).get('assembler') is True

        self.pre_build()
        self.build()
        self.post_build()

        self.add_host_connection_items(self.host_connections_ids)

        if self.host_connection:
            # Prevent the sync calling on creation as host might be already set.
            self._on_client_host_changed_callback()

    def pre_build(self):
        '''Pre-build method of the widget'''
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        '''Build method of the widget'''
        self._header = SessionHeader(self.session)

        self._host_connection_selector = DropdownSelector("Host Selector")

        self.asset_manager_browser = AssetManagerBrowser(
            self._in_assembler, self.event_manager, self._asset_list_model
        )

        self.layout().addWidget(self._header)
        self.layout().addWidget(self._host_connection_selector)
        self.layout().addWidget(self.asset_manager_browser, 100)

    def post_build(self):
        '''Post Build method of the widget'''
        # Connect host selector signals
        self._host_connection_selector.current_item_changed.connect(
            self._on_host_selected_callback
        )
        self._host_connection_selector.refresh_clicked.connect(
            self._on_refresh_hosts_callback
        )
        self.asset_manager_browser.on_config.connect(
            self._on_open_assembler_callback
        )

    def _on_open_assembler_callback(self, event):
        '''Open the assembler dialog'''
        self.event_manager.publish.client_launch_widget(
            self.selected_host_connection_id,
            ftrack_constants.framework.definition.LOADER,
        )

    def show_ui(self):
        '''Override Show method of the base framework dialog'''
        self.show()

    # TODO: this should be an ABC
    def connect_focus_signal(self):
        '''Connect signal when the current dialog gets focus'''
        # Update the is_active property.
        QtWidgets.QApplication.instance().focusChanged.connect(
            self._on_focus_changed
        )

    def add_host_connection_items(self, host_connections_ids):
        '''Add given host_connections in the host_connection selector'''
        for host_connection_id in host_connections_ids:
            self._host_connection_selector.add_item(host_connection_id)

    # TODO: This should be an ABC
    def _on_client_hosts_discovered_callback(self, event=None):
        '''Client new hosts has been discovered'''
        super(AssetManagerDialog, self)._on_client_hosts_discovered_callback(
            event
        )

    def _on_host_selected_callback(self, item_text):
        '''Handle host selection'''
        if not item_text:
            self.host_connection = None
            return

        for host_connection in self.host_connections:
            if host_connection.host_id == item_text:
                self.host_connection = host_connection

    # TODO: This should be an ABC
    def _on_client_host_changed_callback(self, event=None):
        '''Client host has been changed, pick the single definition (should be just one)'''
        super(AssetManagerDialog, self)._on_client_host_changed_callback(event)
        if not self.host_connection:
            self.selected_host_connection_id = None
            return
        self.selected_host_connection_id = self.host_connection.host_id
        assert (
            len(self.definition_names) > 0
        ), 'No asset manager definitions are aviailable!'
        if len(self.definition_names) > 1:
            self.logger.warning(
                'More than one asset manager definitions found ({})!'.format(
                    len(self.definition_names)
                )
            )

        definition_name = self.definition_names[0]

        for definition_list in self.filtered_definitions:
            self.definition = definition_list.get_first(name=definition_name)

        self.build_asset_manager_ui(self.definition)

    def _on_refresh_hosts_callback(self):
        '''
        Refresh host button has been clicked in the UI,
        Call the discover_host in the client
        '''
        self.client_method_connection('discover_hosts')

    # TODO: This should be an ABC
    def sync_host_connection(self):
        '''
        Client host has been changed and doesn't match the ui host when
        focus is back to the current UI
        '''
        if self.host_connection.host_id != self.selected_host_connection_id:
            result = ModalDialog(
                self,
                title='Host connection out of sync!',
                message='Selected host connection is not the current host_connection, '
                'do you want to update UI to sync with the current one?',
                question=True,
            ).exec_()
            if result:
                self._on_client_host_changed_callback()
            else:
                self._on_host_selected_callback(
                    self.selected_host_connection_id
                )

    def build_asset_manager_ui(self, definition):
        '''A definition has been selected, providing the required plugins to drive the asset manager.
        Now build the UI'''

        menu_action_plugins = definition.get('actions')
        self.asset_manager_browser.create_actions(menu_action_plugins, self)
        self.asset_manager_browser.rebuild()

    # Handle asset actions

    def check_selection(self, selected_assets):
        '''Check if *selected_assets* is empty and show dialog message'''
        if len(selected_assets) == 0:
            ModalDialog(
                self._client,
                title='Error!',
                message="Please select at least one asset!",
            ).exec_()
            return False
        else:
            return True

    def ctx_discover(self, selected_assets, plugin):
        print('@@@ ctx_discover: {}'.format(plugin))
