# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.dialogs import ScrollDefinitionsDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget


# TODO: review and docstring this code
class PublisherDialog(FrameworkDialog, ScrollDefinitionsDialog):
    '''Base Class to represent a Plugin'''

    name = 'framework_publisher_dialog'
    definition_filter = ['publisher']
    ui_type = 'qt'

    @property
    def host_connections_ids(self):
        ids = []
        for host_connection in self.host_connections:
            ids.append(host_connection.host_id)
        return ids

    @property
    def definition_names(self):
        names = []
        for definitions in self.filtered_definitions:
            print(definitions)
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
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        ScrollDefinitionsDialog.__init__(self, session=event_manager.session, parent=parent)
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

        self._set_scroll_dialog_connections()

    # TODO: this should be an ABC
    def pre_build(self):
        ScrollDefinitionsDialog.pre_build(self)
        FrameworkDialog.pre_build(self)

    # TODO: this should be an ABC
    def build(self):
        self.run_button_title = 'Publish'
        ScrollDefinitionsDialog.build(self)
        FrameworkDialog.build(self)

    # TODO: this should be an ABC
    def post_build(self):
        ScrollDefinitionsDialog.post_build(self)
        FrameworkDialog.post_build(self)

    def _set_scroll_dialog_connections(self):
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
        self.selected_host_changed.connect(
            self._on_ui_host_changed_callback
        )
        self.selected_definition_changed.connect(
            self._on_ui_definition_changed_callback
        )
        self.refresh_hosts_clicked.connect(
            self._on_ui_refresh_hosts_callback
        )
        self.refresh_definitions_clicked.connect(
            self._on_ui_refresh_definitions_callback
        )
        self.run_button_clicked.connect(
            self._on_ui_run_button_clicked_callback
        )

    # TODO: this should be an ABC
    def show(self):
        ScrollDefinitionsDialog.show(self)

    # TODO: this should be an ABC
    def connect_focus_signal(self):
        # Update the is_active property.
        QtWidgets.QApplication.instance().focusChanged.connect(
            self._on_focus_changed
        )

    # TODO: This should be an ABC
    def _on_client_context_changed_callback(self, event=None):
        super(PublisherDialog, self)._on_client_context_changed_callback(event)
        self.selected_context_id = self.context_id

    # TODO: This should be an ABC
    def _on_client_hosts_discovered_callback(self, event=None):
        super(PublisherDialog, self)._on_client_hosts_discovered_callback(event)

    # TODO: This should be an ABC
    def _on_client_host_changed_callback(self, event=None):
        super(PublisherDialog, self)._on_client_host_changed_callback(event)
        self.selected_host_connection_id = self.host_connection.host_id
        self.add_definition_items(self.definition_names)

    # TODO: This should be an ABC
    def _on_client_definition_changed_callback(self, event=None):
        super(PublisherDialog, self)._on_client_definition_changed_callback(event)
        definition_name = None
        if self.definition:
            definition_name = self.definition.name
        self.selected_definition_name = definition_name
        self.build_definition_ui(self.definition)

        # TODO: This should be an ABC

    # TODO: This should be an ABC
    def sync_context(self):
        if self.is_browsing_context:
            return
        if self.context_id != self.selected_context_id:
            result = self.show_message_dialog(
                title='Context out of sync!',
                message='Selected context is not the current context, '
                        'do you want to update UI to syc with the current context?',
                button_1_text='Update',
                button_2_text='Keep Current',
            )
            if result == 1:
                self._on_client_context_changed_callback()
            elif result == 0:
                self._on_ui_context_changed_callback(
                    self.selected_context_id
                )

    # TODO: This should be an ABC
    def sync_host_connection(self):
        if (
                self.host_connection.host_id
                != self.selected_host_connection_id
        ):
            result = self.show_message_dialog(
                title='Host connection out of sync!',
                message='Selected host connection is not the current host_connection, '
                        'do you want to update UI to sync with the current one?',
                button_1_text='Update',
                button_2_text='Keep Current',
            )
            if result == 1:
                self._on_client_host_changed_callback()
            elif result == 0:
                self._on_ui_host_changed_callback(
                    self.selected_host_connection_id
                )

    # TODO: This should be an ABC
    def sync_definition(self):
        sync = False
        if not self.definition and self.selected_definition_name:
            sync = True
        else:
            if (
                    self.definition.name
                    != self.selected_definition_name
            ):
                match = False
                for definition_list in self.filtered_definitions:
                    definition = definition_list.get_first(
                        name=self.definition.name
                    )
                    if definition:
                        match = True
                        sync = True
                        break
                if not match:
                    # Automatically sync current definition to client as the current
                    # definition is not available for this UI.
                    self._on_ui_definition_changed_callback(
                        self.selected_definition_name
                    )
                    return
        if sync:
            result = self.show_message_dialog(
                title='Current definition is out of sync!',
                message='Selected definition is not the current definition, '
                        'do you want to update UI to sync with the current one?',
                button_1_text='Update',
                button_2_text='Keep Current',
            )
            if result == 1:
                self._on_client_definition_changed_callback()
            elif result == 0:
                self._on_ui_definition_changed_callback(
                    self.selected_definition_name
                )

    # TODO: maybe move this to a utils and standarize icon.
    def show_message_dialog(
            self, title, message, button_1_text, button_2_text
    ):
        message_box = QtWidgets.QMessageBox()
        message_box.setWindowTitle(title)
        message_box.setText(message)
        message_box.setIcon(QtWidgets.QMessageBox.Question)
        message_box.addButton(button_1_text, QtWidgets.QMessageBox.YesRole)
        message_box.addButton(button_2_text, QtWidgets.QMessageBox.NoRole)
        result = message_box.exec_()
        return result

    def _on_ui_context_changed_callback(self, context_id):
        self.context_id = context_id

    def _on_ui_host_changed_callback(self, host_id):
        for host_connection in self.host_connections:
            if host_connection.host_id == host_id:
                self.host_connection = host_connection
                self.add_definition_items(self.definition_names)

    def _on_ui_definition_changed_callback(self, definition_name):
        for definition_list in self.filtered_definitions:
            definition = definition_list.get_first(name=definition_name)
            self.definition = definition
            self.build_definition_ui(self.definition)

    def _on_ui_refresh_hosts_callback(self):
        self.client_method_connection('discover_hosts')
        self.add_host_connection_items(self.host_connections_ids)

    def _on_ui_refresh_definitions_callback(self):
        self.client_method_connection('discover_hosts')
        self.add_definition_items(self.definition_names)

    def build_definition_ui(self, definition):
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
            step_accordion_widget = AccordionBaseWidget(
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
        arguments = {
            "definition": self.definition,
            "engine_type": self.client_property_getter_connection(
                'engine_type'
            ),
        }
        self.client_method_connection('run_definition', arguments=arguments)

    def run_collectors(self, plugin_widget_id=None):
        collector_plugins = self.definition.get_all(
            category='plugin', type='collector'
        )
        for collector_plugin in collector_plugins:
            arguments = {
                "plugin_definition": collector_plugin,
                "plugin_method_name": 'run',
                "engine_type": self.definition['_config']['engine_type'],
                'plugin_widget_id': plugin_widget_id,
            }
            self.client_method_connection('run_plugin', arguments=arguments)
