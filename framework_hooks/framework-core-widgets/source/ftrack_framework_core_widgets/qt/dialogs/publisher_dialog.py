# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.dialogs import ScrollDefinitionsDialog
from ftrack_qt.widgets.dialogs import ModalDialog
from ftrack_qt.widgets.accordion import PublisherAccordionWidget


class PublisherDialog(FrameworkDialog, ScrollDefinitionsDialog):
    '''Default Framework Publisher widget'''

    name = 'framework_publisher_dialog'
    definition_type_filter = ['publisher']
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
    def definition_names(self):
        '''Returns available definition names in the client'''
        names = []
        for definitions in self.filtered_definitions:
            for definition in definitions:
                names.append(definition.name)
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
        ScrollDefinitionsDialog.__init__(
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
        self.selected_definition_changed.connect(
            self._on_ui_definition_changed_callback
        )
        self.refresh_hosts_clicked.connect(self._on_ui_refresh_hosts_callback)
        self.refresh_definitions_clicked.connect(
            self._on_ui_refresh_definitions_callback
        )
        self.run_button_clicked.connect(
            self._on_ui_run_button_clicked_callback
        )

    # TODO: this should be an ABC
    def show_ui(self):
        '''Override Show method of the base framework dialog'''
        ScrollDefinitionsDialog.show(self)

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
        super(PublisherDialog, self)._on_client_context_changed_callback(event)
        self.selected_context_id = self.context_id

    # TODO: This should be an ABC
    def _on_client_hosts_discovered_callback(self, event=None):
        '''Client new hosts has been discovered'''
        super(PublisherDialog, self)._on_client_hosts_discovered_callback(
            event
        )

    # TODO: This should be an ABC
    def _on_client_host_changed_callback(self, event=None):
        '''Client host has been changed'''
        super(PublisherDialog, self)._on_client_host_changed_callback(event)
        if not self.host_connection:
            self.selected_host_connection_id = None
            return
        self.selected_host_connection_id = self.host_connection.host_id
        self.add_definition_items(self.definition_names)

    # TODO: This should be an ABC
    def _on_definition_changed_callback(self):
        '''The selected definition has been changed'''
        super(PublisherDialog, self)._on_definition_changed_callback()
        definition_name = None
        if self.definition:
            definition_name = self.definition.name
        self.selected_definition_name = definition_name
        if self.selected_definition_name:
            self.build_definition_ui(self.definition)

    # TODO: This should be an ABC
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

    def _on_ui_definition_changed_callback(self, definition_name):
        '''Definition has been changed in the ui.'''
        if not definition_name:
            self.definition = None
            return
        for definition_list in self.filtered_definitions:
            definition = definition_list.get_first(name=definition_name)
            self.definition = definition

    def _on_ui_refresh_hosts_callback(self):
        '''
        Refresh host button has been clicked in the UI,
        Call the discover_host in the client
        '''
        self.client_method_connection('discover_hosts')

    def _on_ui_refresh_definitions_callback(self):
        '''
        Refresh definitions button has been clicked in the UI,
        Call the discover_host in the client
        '''
        self.client_method_connection('discover_hosts')

    def build_definition_ui(self, definition):
        '''A definition has been selected, build the definition widget.'''
        # Build context widgets
        context_plugins = definition.get_all(category='plugin', type='context')
        for context_plugin in context_plugins:
            if not context_plugin.widget:
                continue
            context_widget = self.init_framework_widget(context_plugin)
            self.definition_widget.layout().addWidget(context_widget)
        # Build component widgets
        component_steps = definition.get_all(category='step', type='component')
        for step in component_steps:
            # TODO: add a key visible in the definition to hide the step if wanted.
            step_accordion_widget = PublisherAccordionWidget(
                selectable=False,
                show_checkbox=True,
                checkable=not step.optional,
                title=step.name,
                selected=False,
                checked=step.enabled,
                collapsable=True,
                collapsed=True,
            )
            step_plugins = step.get_all(category='plugin')
            for step_plugin in step_plugins:
                if not step_plugin.widget:
                    continue
                widget = self.init_framework_widget(step_plugin)
                if step_plugin.type == 'collector':
                    step_accordion_widget.add_widget(widget)
                if step_plugin.type == 'validator':
                    step_accordion_widget.add_option_widget(
                        widget, section_name='Validators'
                    )
                if step_plugin.type == 'exporter':
                    step_accordion_widget.add_option_widget(
                        widget, section_name='Exporters'
                    )
            self._definition_widget.layout().addWidget(step_accordion_widget)

    def _on_ui_run_button_clicked_callback(self):
        '''
        Run button from the UI has been clicked.
        Tell client to run the current definition
        '''

        arguments = {
            "definition": self.definition,
            "engine_type": self.definition.engine_type,
            "engine_name": self.definition.engine_name,
        }
        self.client_method_connection('run_definition', arguments=arguments)

    def run_collectors(self, plugin_widget_id=None):
        '''
        Run all the collector plugins of the current definition.
        If *plugin_widget_id* is given, a signal with the result of the plugins
        will be emitted to be picked by that widget id.
        '''
        collector_plugins = self.definition.get_all(
            category='plugin', type='collector'
        )
        for collector_plugin in collector_plugins:
            arguments = {
                "plugin_definition": collector_plugin,
                "plugin_method_name": 'run',
                "engine_type": self.definition.engine_type,
                "engine_name": self.definition.engine_name,
                'plugin_widget_id': plugin_widget_id,
            }
            self.client_method_connection('run_plugin', arguments=arguments)
