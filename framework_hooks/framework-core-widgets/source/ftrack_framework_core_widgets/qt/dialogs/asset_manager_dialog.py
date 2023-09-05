# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.dialogs import StyledDialog, ModalDialog
from ftrack_qt.widgets.browsers import AssetManagerBrowser
from ftrack_qt.model.asset_list import AssetListModel

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
        # TODO: convert this to a property and align the code to scroll_definitions_dialog
        self.selected_host_connection_id = None
        self._asset_manager_browser = None
        # TODO: instead of passing the model around, We get the discovered assets
        #  from the discover plugin, we store those asset_info in the result of the
        #  plugin registry. So when Assembler opens, it checks if the discover plugin
        #  of the AM has been run: if has results, pick the results and generate
        #  the model from those results.
        #  If not result: run discover AM plugin and check results again. So _asset_list_model will not apear at all in this dialog, we will simply pass asste_infos around until they arrive to the
        self._asset_list_model = (dialog_options or {}).get('model')
        # TODO: if not
        if self._asset_list_model is None:
            self.logger.warning('No global asset list model provided, creating.')
            self._asset_list_model = AssetListModel()
        # TODO: maybe not need to pass in assembler? so the asset_manager_dialog
        #  is never used inside the assembler, but the AssetManagerBrowser can
        #  be initialized in the assembler, so then, just set the argument
        #  in_assembler of the assetmbler to default as False, and when you
        #  initialize the browser in the assembler you pass the argument as True.
        self._in_assembler = (dialog_options or {}).get('assembler') is True

    def pre_build(self):
        '''Pre-build method of the widget'''
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.asset_manager_browser = AssetManagerBrowser(
            self._in_assembler,
            self.event_manager,
            self._asset_list_model
        )

    def build(self):
        '''Build method of the widget'''

        self._host_connection_selector = ListSelector("Host Selector")

        self.layout().addWidget(self._header)
        self.layout().addWidget(self._host_connection_selector)
        self.layout().addWidget(self.asset_manager_browser, 100)

    def post_build(self):
        '''Post Build method of the widget'''
        # Connect host selector signals
        self._host_connection_selector.current_item_changed.connect(
            self._on_host_selected_callback
        )

    def _on_host_selected_callback(self, item_text):
        '''
        Emit signal with the new selected host_id
        '''

        if not item_text:
            self.host_connection = None
            return

        for host_connection in self.host_connections:
            if host_connection.host_id == item_text:
                self.host_connection = host_connection

    # TODO: this should be an ABC
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

    # TODO: This should be an ABC
    def _on_client_context_changed_callback(self, event=None):
        '''Client context has been changed'''
        super(AssetManagerDialog, self)._on_client_context_changed_callback(event)
        self.selected_context_id = self.context_id

    # TODO: This should be an ABC
    def _on_client_hosts_discovered_callback(self, event=None):
        '''Client new hosts has been discovered'''
        super(AssetManagerDialog, self)._on_client_hosts_discovered_callback(
            event
        )

    # TODO: This should be an ABC
    def _on_client_host_changed_callback(self, event=None):
        '''Client host has been changed, pick the single definition (should be just one)'''
        super(AssetManagerDialog, self)._on_client_host_changed_callback(event)
        if not self.host_connection:
            self.selected_host_connection_id = None
            return
        self.selected_host_connection_id = self.host_connection.host_id
        assert (len(self.definition_names) > 0), 'No asset manager definitions are aviailable!'
        if len(self.definition_names) > 1:
            self.logger.warning('More than one asset manager definitions found ({})!'.format(
                len(self.definition_names)))
        definition_name = self.definition_names[0]

        for definition_list in self.filtered_definitions:
            self.definition = definition_list.get_first(name=definition_name)

        self.build_asset_manager_ui(self.definition)

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
                self._on_ui_host_changed_callback(
                    self.selected_host_connection_id
                )

    def build_asset_manager_ui(self, definition):
        '''A definition has been selected, providing the required plugins to drive the asset manager.
        Now build the UI'''

        menu_action_plugins = definition.get('actions')
        self.asset_manager_browser.create_actions(menu_action_plugins, self)


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