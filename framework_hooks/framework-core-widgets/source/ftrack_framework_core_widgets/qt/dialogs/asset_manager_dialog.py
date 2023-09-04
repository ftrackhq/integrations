# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.dialogs import StyledDialog, ModalDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget


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
    def definition_names(self):
        '''Returns available definition names in the client'''
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

    def pre_build(self):
        '''Pre build method of the widget'''
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        '''Build method of the widget'''

        self._host_connection_selector = ListSelector("Host Selector")

        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )

        self.layout().addWidget(self._header)
        self.layout().addWidget(self._host_connection_selector)
        self.layout().addWidget(self._scroll_area, 100)
        #self._scroll_area.setWidget(self._definition_widget)

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
        self.build_asset_manager_ui()

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
        '''
        Run button from the UI has been clicked.
        Tell client to run the current definition
        '''

        arguments = {
            "definition": self.definition,
            "engine_type": self.client_property_getter_connection(
                'engine_type'
            ),
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
                "engine_type": self.definition['_config']['engine_type'],
                'plugin_widget_id': plugin_widget_id,
            }
            self.client_method_connection('run_plugin', arguments=arguments)
