# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.dialogs import ScrollToolConfigsDialog
from ftrack_qt.widgets.dialogs import ModalDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget


class PublisherDialog(FrameworkDialog, ScrollToolConfigsDialog):
    '''Default Framework Publisher widget'''

    name = 'framework_publisher_dialog'
    tool_config_type_filter = ['publisher']
    ui_type = 'qt'
    docked = True

    @property
    def host_connections_ids(self):
        '''Returns available host id in the client'''
        ids = []
        for host_connection in self.host_connections:
            ids.append(host_connection.host_id)
        return ids

    @property
    def tool_config_names(self):
        '''Returns available tool config names in the client'''
        names = []
        for tool_configs in self.filtered_tool_configs:
            print(tool_configs)
            for tool_config in tool_configs:
                names.append(tool_config.tool_title)
        return names

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
        Initialize Mixin clas publisher dialog. It will load the qt dialog and
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
        ScrollToolConfigsDialog.__init__(
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
        # This is in a separated method and not in the post_build because the
        # BaseFrameworkDialog should be initialized before starting with these
        # connections.
        self._set_scroll_dialog_connections()

    def pre_build(self):
        '''Pre Build method of the widget'''
        super(PublisherDialog, self).pre_build()

    def build(self):
        '''Build method of the widget'''
        self.run_button_title = 'Publish'
        super(PublisherDialog, self).build()

    def post_build(self):
        '''Post Build method of the widget'''
        super(PublisherDialog, self).post_build()

    def _set_scroll_dialog_connections(self):
        '''Create all the connections to communicate to the scroll widget'''
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
        self.selected_tool_config_changed.connect(
            self._on_ui_tool_config_changed_callback
        )
        self.refresh_hosts_clicked.connect(self._on_ui_refresh_hosts_callback)
        self.refresh_tool_configs_clicked.connect(
            self._on_ui_refresh_tool_configs_callback
        )
        self.run_button_clicked.connect(
            self._on_ui_run_button_clicked_callback
        )

    def show_ui(self):
        '''Override Show method of the base framework dialog'''
        ScrollToolConfigsDialog.show(self)

    def connect_focus_signal(self):
        '''Connect signal when the current dialog gets focus'''
        # Update the is_active property.
        QtWidgets.QApplication.instance().focusChanged.connect(
            self._on_focus_changed
        )

    def _on_client_context_changed_callback(self, event=None):
        '''Client context has been changed'''
        super(PublisherDialog, self)._on_client_context_changed_callback(event)
        self.selected_context_id = self.context_id

    def _on_client_hosts_discovered_callback(self, event=None):
        '''Client new hosts has been discovered'''
        super(PublisherDialog, self)._on_client_hosts_discovered_callback(
            event
        )

    def _on_client_host_changed_callback(self, event=None):
        '''Client host has been changed'''
        super(PublisherDialog, self)._on_client_host_changed_callback(event)
        if not self.host_connection:
            self.selected_host_connection_id = None
            return
        self.selected_host_connection_id = self.host_connection.host_id
        self.add_tool_config_items(self.tool_config_names)

    def _on_tool_config_changed_callback(self):
        '''The selected tool config has been changed'''
        super(PublisherDialog, self)._on_tool_config_changed_callback()
        tool_config_name = None
        if self.tool_config:
            tool_config_name = self.tool_config.tool_title
        self.selected_tool_config_name = tool_config_name
        if self.selected_tool_config_name:
            self.build_tool_config_ui(self.tool_config)

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

    def _on_ui_tool_config_changed_callback(self, tool_config_name):
        '''Tool config has been changed in the ui.'''
        if not tool_config_name:
            self.tool_config = None
            return
        for tool_config_list in self.filtered_tool_configs:
            tool_config = tool_config_list.get_first(
                tool_title=tool_config_name
            )
            self.tool_config = tool_config

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

    def build_tool_config_ui(self, tool_config):
        '''A tool config has been selected, build the tool config widget.'''
        # Build context widgets
        context_plugins = tool_config.get_all(
            category='plugin', plugin_type='context'
        )
        for context_plugin in context_plugins:
            if not context_plugin.widget_name:
                continue
            context_widget = self.init_framework_widget(context_plugin)
            self.tool_config_widget.layout().addWidget(context_widget)
        # Build component widgets
        component_steps = tool_config.get_all(
            category='step', step_type='component'
        )
        for step in component_steps:
            # TODO: add a key visible in the tool config to hide the step if wanted.
            step_accordion_widget = AccordionBaseWidget(
                selectable=False,
                show_checkbox=True,
                checkable=not step.optional,
                title=step.step_name,
                selected=False,
                checked=step.enabled,
                collapsable=True,
                collapsed=True,
            )
            step_plugins = step.get_all(category='plugin')
            for step_plugin in step_plugins:
                if not step_plugin.widget_name:
                    continue
                widget = self.init_framework_widget(step_plugin)
                if step_plugin.plugin_type == 'collector':
                    step_accordion_widget.add_widget(widget)
                if step_plugin.plugin_type == 'validator':
                    step_accordion_widget.add_option_widget(
                        widget, section_name='Validators'
                    )
                if step_plugin.plugin_type == 'exporter':
                    step_accordion_widget.add_option_widget(
                        widget, section_name='Exporters'
                    )
            self._tool_config_widget.layout().addWidget(step_accordion_widget)

    def _on_ui_run_button_clicked_callback(self):
        '''
        Run button from the UI has been clicked.
        Tell client to run the current tool config
        '''

        arguments = {"tool_config": self.tool_config}
        self.client_method_connection('run_tool_config', arguments=arguments)

    def run_collectors(self, plugin_widget_id=None):
        '''
        Run all the collector plugins of the current tool_config.
        If *plugin_widget_id* is given, a signal with the result of the plugins
        will be emitted to be picked by that widget id.
        '''
        collector_plugins = self.tool_config.get_all(
            category='plugin', plugin_type='collector'
        )
        for collector_plugin in collector_plugins:
            arguments = {
                "plugin_config": collector_plugin,
                "plugin_method_name": 'run',
                "engine_type": self.tool_config.engine_type,
                "engine_name": self.tool_config.engine_name,
                'plugin_widget_id': plugin_widget_id,
            }
            self.client_method_connection('run_plugin', arguments=arguments)
