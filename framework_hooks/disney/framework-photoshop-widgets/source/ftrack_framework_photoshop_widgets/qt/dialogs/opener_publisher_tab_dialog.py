# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.dialogs import TabDialog
from ftrack_qt.widgets.dialogs import ModalDialog


class OpenerPublisherTabDialog(FrameworkDialog, TabDialog):
    '''Default Framework Publisher widget'''

    name = 'framework_opener_publisher_tab_dialog'
    tool_config_type_filter = ['publisher', 'opener']
    ui_type = 'qt'
    docked = False

    @property
    def tab_mapping(self):
        return self._tab_mapping

    @property
    def host_connections_ids(self):
        '''Returns available host id in the client'''
        ids = []
        for host_connection in self.host_connections:
            ids.append(host_connection.host_id)
        return ids

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
        # As a mixing class we have to initialize the parents separately
        TabDialog.__init__(
            self,
            session=event_manager.session,
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
        self.host_connection_selector.hide()
        self._asset_collector_widget = None
        self._tab_mapping = {}
        # This is in a separated method and not in the post_build because the
        # BaseFrameworkDialog should be initialized before starting with these
        # connections.
        self._set_tab_dialog_connections()

        self._pre_select_tool_configs()
        self._build_tabs()

    def _pre_select_tool_configs(self):
        '''Pre-select the desired tool configs'''
        # Pre-select desired tool-configs
        opener_tool_configs = self.filtered_tool_configs['opener']
        if opener_tool_configs:
            # Pick the first tool config available
            self._tab_mapping['open'] = opener_tool_configs.get_first(
                tool_title="Document Opener"
            )
            if not self.tool_config:
                self.tool_config = self._tab_mapping['open']

        publisher_tool_configs = self.filtered_tool_configs['publisher']
        if publisher_tool_configs:
            # Pick the first tool config available
            self._tab_mapping['save'] = publisher_tool_configs.get_first(
                tool_title="Document Publisher"
            )
            if not self.tool_config:
                self.tool_config = self._tab_mapping['save']

    def _build_tabs(self):
        '''Build Open and save tabs'''
        if self._tab_mapping['open']:
            self._open_widget = self._build_open_widget()
            self.add_tab("Open", self._open_widget)
            for widget in self.framework_widgets.values():
                if widget.name == 'asset_version_browser_collector':
                    self._asset_collector_widget = widget
                    widget.fetch_asset_versions()

        if self._tab_mapping['save']:
            # TODO: to be implemented
            self._publish_widget = self._build_publish_widget()
            self.add_tab("Save", self._publish_widget)

    def _build_open_widget(self):
        '''Open tab widget creation'''
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Build Collector widget
        collector_plugins = self.tab_mapping['open'].get_all(
            category='plugin', plugin_type='collector'
        )
        for collector_plugin_config in collector_plugins:
            if not collector_plugin_config.widget_name:
                continue
            collector_widget = self.init_framework_widget(
                collector_plugin_config
            )
            main_widget.layout().addWidget(collector_widget)

        open_button = QtWidgets.QPushButton('Open')

        open_button.clicked.connect(self._on_ui_open_button_clicked_callback)

        main_widget.layout().addWidget(open_button)

        return main_widget

    def _build_publish_widget(self):
        '''Open tab widget creation'''
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Build Collector widget
        context_plugins = self.tab_mapping['save'].get_all(
            category='plugin', plugin_type='context'
        )
        for context_plugin_config in context_plugins:
            if not context_plugin_config.widget_name:
                continue
            context_widget = self.init_framework_widget(context_plugin_config)
            main_widget.layout().addWidget(context_widget)

        buttons_layout = QtWidgets.QHBoxLayout()
        # TODO: version up could execute a plugin defined in plugins of the tool-config
        # version_up_button = QtWidgets.QPushButton('Version Up')
        # TODO: review executes the entire tool-config steps/stages
        review_button = QtWidgets.QPushButton('Send to Review')

        review_button.clicked.connect(
            self._on_ui_review_button_clicked_callback
        )

        # buttons_layout.addWidget(version_up_button)
        buttons_layout.addWidget(review_button)
        main_widget.layout().addLayout(buttons_layout)

        return main_widget

    def _set_tab_dialog_connections(self):
        '''Create all the connections to communicate to the TabDialog'''
        # Set context from client:
        self._on_client_context_changed_callback()

        # Add host connection items
        self.add_host_connection_items(self.host_connections_ids)

        if self.host_connection:
            # Prevent the sync calling on creation as host might be already set.
            self._on_client_host_changed_callback()

        self.selected_context_changed.connect(
            self._on_ui_context_changed_callback
        )
        self.selected_host_changed.connect(self._on_ui_host_changed_callback)

        self.selected_tab_changed.connect(
            self._on_selected_tab_changed_callback
        )

        self.refresh_hosts_clicked.connect(self._on_ui_refresh_hosts_callback)

    def show_ui(self):
        '''Override Show method of the base framework dialog'''
        TabDialog.show(self)
        self.raise_()
        self.activateWindow()
        self.setWindowState(
            self.windowState() & ~QtCore.Qt.WindowMinimized
            | QtCore.Qt.WindowActive
        )

    def connect_focus_signal(self):
        '''Connect signal when the current dialog gets focus'''
        # Update the is_active property.
        QtWidgets.QApplication.instance().focusChanged.connect(
            self._on_focus_changed
        )

    def _on_client_context_changed_callback(self, event=None):
        '''Client context has been changed'''
        super(
            OpenerPublisherTabDialog, self
        )._on_client_context_changed_callback(event)
        self.selected_context_id = self.context_id

    def _on_client_hosts_discovered_callback(self, event=None):
        '''Client new hosts has been discovered'''
        super(
            OpenerPublisherTabDialog, self
        )._on_client_hosts_discovered_callback(event)

    def _on_client_host_changed_callback(self, event=None):
        '''Client host has been changed'''
        super(OpenerPublisherTabDialog, self)._on_client_host_changed_callback(
            event
        )
        if not self.host_connection:
            self.selected_host_connection_id = None
            return
        self.selected_host_connection_id = self.host_connection.host_id

    def _on_selected_tab_changed_callback(self, tab_name):
        self.tool_config = self.tab_mapping.get(tab_name.lower())

    def sync_context(self):
        '''
        Client context has been changed and doesn't match the ui context when
        focus is back to the current UI
        '''
        if self.is_browsing_context:
            return
        if self.context_id != self.selected_context_id:
            result = ModalDialog(
                self,
                title='Context out of sync!',
                message='Selected context is not the current context, '
                'do you want to update UI to syc with the current context?',
                question=True,
            ).exec_()
            if result:
                self._on_client_context_changed_callback()
            else:
                self._on_ui_context_changed_callback(self.selected_context_id)

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

    def _on_ui_context_changed_callback(self, context_id):
        '''Context has been changed in the ui. Passing it to the client'''
        self.context_id = context_id

    def _on_ui_host_changed_callback(self, host_id):
        '''Host has been changed in the ui. Passing it to the client'''
        if not host_id:
            self.host_connection = None
            return
        for host_connection in self.host_connections:
            if host_connection.host_id == host_id:
                self.host_connection = host_connection

    def _on_ui_refresh_hosts_callback(self):
        '''
        Refresh host button has been clicked in the UI,
        Call the discover_host in the client
        '''
        self.client_method_connection('discover_hosts')

    def _on_ui_refresh_tool_configs_callback(self):
        '''
        Refresh tool_configs button has been clicked in the UI,
        Call the discover_host in the client
        '''
        self.client_method_connection('discover_hosts')

    def _on_ui_open_button_clicked_callback(self):
        '''
        Open button from the UI has been clicked.
        Tell client to run the current tool config
        '''
        selected_assets = self._asset_collector_widget.selected_assets
        if not selected_assets:
            ModalDialog(
                self,
                title='No assets selected!',
                message='Please select the desired assets to open',
                question=False,
            ).exec_()
            return

        self._run_tool_config()

    def _on_ui_review_button_clicked_callback(self):
        '''
        Open button from the UI has been clicked.
        Tell client to run the current tool config
        '''
        self._run_tool_config()

    def _run_tool_config(self):
        '''
        Open button from the UI has been clicked.
        Tell client to run the current tool config
        '''
        arguments = {"tool_config": self.tool_config}
        self.client_method_connection('run_tool_config', arguments=arguments)
