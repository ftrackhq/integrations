# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import uuid

from ftrack_framework_widget import Base, active_widget


class Dialog(Base):
    '''Base Class to represent a Plugin'''

    # We Define name, plugin_type and host_type as class variables for
    # convenience for the user when creating its own plugin.
    name = None
    widget_type = 'framework_dialog'
    client_method_connection = None
    client_property_setter_connection = None
    client_property_getter_connection = None

    @property
    def definitions(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('definitions')

    @property
    def definition(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('definition')

    @definition.setter
    def definition(self, value):
        '''
        Dependency framework widgets
        '''
        self.client_property_setter_connection('definition', value)

    @property
    def context_id(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('context_id')

    @context_id.setter
    def context_id(self, value):
        '''
        Dependency framework widgets
        '''
        self.client_property_setter_connection('context_id', value)

    @property
    def host_connection(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('host_connection')

    @host_connection.setter
    def host_connection(self, value):
        '''
        Dependency framework widgets
        '''
        self.client_property_setter_connection('host_connection', value)

    @property
    def host_connections(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('host_connections')

    @property
    def plugins(self):
        '''
        Dependency framework widgets
        '''
        if not self.definition:
            self.logger.warning("Please set a definition before quering plugins")
            return None
        return self.definition.get_all(category='plugin')

    @property
    def framework_widgets(self):
        '''
        Dependency framework widgets
        '''
        return self.__framework_widget_registry

    def __init__(
            self,
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=None
    ):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        # Set properties to 0
        self._definitions = None
        self._host_connections = None
        self._definition = None
        self._host_connection = None
        self.__framework_widget_registry = {}

        # TODO: implement dialog_options

        # Connect client methods and properties
        # TODO: should this be by events?
        self.connect_methods(connect_methods_callback)
        self.connect_properties(
            connect_setter_property_callback,
            connect_getter_property_callback
        )
        self._dialog_options = dialog_options

        super(Dialog, self).__init__(event_manager, client_id, parent)

    def connect_methods(self, method):
        # TODO: should this be subscription events?
        self.client_method_connection = method

    def connect_properties(self, set_method, get_method):
        # TODO: should this be subscription events?
        self.client_property_setter_connection = set_method
        self.client_property_getter_connection = get_method

    def _subscribe_client_events(self):
        self.event_manager.subscribe.client_signal_context_changed(
            self.client_id,
            callback=self._on_client_context_changed_callback
        )
        self.event_manager.subscribe.client_signal_hosts_discovered(
            self.client_id,
            callback=self._on_client_hosts_discovered_callback
        )
        self.event_manager.subscribe.client_signal_host_changed(
            self.client_id,
            callback=self._on_client_host_changed_callback
        )
        # TODO: I think this one is not needed as when host is changed new definitions are discovered. And if context id is changed also new definitions are discovered.
        # self.event_manager.subscribe.client_notify_definitions_discovered(
        #     self.client_id,
        #     callback=self._on_client_context_changed_callback
        # )
        self.event_manager.subscribe.client_signal_definition_changed(
            self.client_id,
            callback=self._on_client_definition_changed_callback
        )
        self.event_manager.subscribe.client_notify_ui_run_plugin_result(
            self.client_id,
            callback=self._on_client_notify_ui_run_plugin_result_callback
        )

    # TODO: this should be an ABC
    def pre_build(self):
        pass

    # TODO: this should be an ABC
    def build(self):
        pass

    # TODO: this should be an ABC
    def post_build(self):
        pass

    # TODO: this should be an ABC
    @active_widget
    def _on_client_context_changed_callback(self, event=None):
        '''Will only run if the widget is active'''
        for id, widget in self.framework_widgets.items():
            widget.update_context(self.context_id)

    # TODO: This should be an ABC
    @active_widget
    def _on_client_hosts_discovered_callback(self, event=None):
        pass

    # TODO: This should be an ABC
    @active_widget
    def _on_client_host_changed_callback(self, event=None):
        # TODO: carefully, here we should update definitions!
        pass

    # TODO: This should be an ABC
    @active_widget
    def _on_client_definition_changed_callback(self, event=None):
        pass

    def _on_focus_changed(self, old_widget, new_widget):
        if self == old_widget:
            self.is_active = False
        elif self == new_widget:
            self.is_active = True
        else:
            self.is_active = False
        if self.is_active:
            # Syncronize context with client
            self.sync_context()
            # Syncronize Host connection with client
            self.sync_host_connection()
            # Syncronize definitiion with client
            self.sync_definition()

    # TODO: this should be an ABC
    def sync_context(self):
        '''
        Check if selected UI context_id is not sync with the client and sync them.
        Pseudo code example PySide UI:
            if self.context_id not is self.context_Selector.current_text():
                raise confirmation widget to decide which one to keep
                equal self.context_Selector.current_text() to self.context_id or
                the other way around depending on the confirmation widget response
        '''
        pass

    # TODO: this should be an ABC
    def sync_host_connection(self):
        '''
        Check if UI selected host_connection is not sync with the client and sync them.
        '''
        pass

    # TODO: this should be an ABC
    def sync_definition(self):
        '''
        Check if UI selected definition is not sync with the client and sync them.
        We usually want to keep the selected Definition
        '''
        pass

    def init_framework_widget(self, plugin_definition):
        widget = plugin_definition.widget(
            self.event_manager,
            self.client_id,
            self.context_id,
            plugin_definition,
            dialog_run_plugin_method_callback=self._connect_run_plugin_method_callback,
            dialog_property_getter_connection_callback=self._connect_dialog_property_getter_connection_callback,
        )
        self._register_widget(widget)
        return widget

    def _register_widget(self, widget):
        if widget.id not in list(self.__framework_widget_registry.keys()):
            self.__framework_widget_registry[widget.id] = widget

    def _connect_run_plugin_method_callback(
            self, plugin_definition, plugin_method_name, plugin_widget_id
    ):
        # No callback as it is async so its returned by an event
        self.run_plugin_method(
            plugin_definition, plugin_method_name, plugin_widget_id
        )

    def _connect_dialog_property_getter_connection_callback(self, property_name):
        return self.__getattribute__(property_name)


    def run_plugin_method(
            self, plugin_definition, plugin_method_name, plugin_widget_id=None
    ):
        # No callback as it is returned by an event
        arguments = {
            "plugin_definition": plugin_definition,
            "plugin_method": plugin_method_name,
            "engine_type": self.definition['_config']['engine_type'],
            'plugin_widget_id': plugin_widget_id
        }
        self.client_method_connection('run_plugin', arguments=arguments)

    def _on_client_notify_ui_run_plugin_result_callback(self, event):
        plugin_info = event['data']
        plugin_widget_id = plugin_info['widget_id']
        widget = self.framework_widgets.get(plugin_widget_id)
        widget.run_plugin_callback(plugin_info)




