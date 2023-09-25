# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_widget import BaseUI, active_widget


class FrameworkDialog(BaseUI):
    '''
    Base Class to represent a FrameworkDilog, all the dialogs executed by the
    UI should inherit from here.
    '''

    name = None
    widget_type = 'framework_dialog'
    client_method_connection = None
    client_property_setter_connection = None
    client_property_getter_connection = None
    tool_config_type_filter = None

    @property
    def tool_configs(self):
        '''
        Available tool_configs in client
        '''
        return self.client_property_getter_connection('tool_configs')

    @property
    def filtered_tool_configs(self):
        '''
        Return tool_configs of types that match the tool_config_type_filter
        '''
        if not self.tool_config_type_filter:
            return list(self.tool_configs.values())
        tool_configs = []
        for tool_config_type in self.tool_config_type_filter:
            tool_configs.append(self.tool_configs.get(tool_config_type))
        return tool_configs

    @property
    def tool_config(self):
        '''Returns the current selected tool_config.'''
        return self._tool_config

    @tool_config.setter
    def tool_config(self, value):
        '''
        Set the given *value* as tool_config if value.name found in
        self.tool_configs
        '''

        if value and not self.tool_configs[value.tool_type].get_first(
            tool_title=value.tool_title
        ):
            self.logger.error(
                "Invalid tool_config, choose one from : {}".format(
                    self.tool_configs
                )
            )
            return

        self._tool_config = value
        # Call _on_tool_config_changed_callback to let the UI know that a new
        # tool_config has been set.
        self._on_tool_config_changed_callback()

    @property
    def context_id(self):
        '''
        Current context id in client
        '''
        return self.client_property_getter_connection('context_id')

    @context_id.setter
    def context_id(self, value):
        '''
        Set the *value* as current context id in client
        '''
        self.client_property_setter_connection('context_id', value)

    @property
    def host_connection(self):
        '''
        Current host connection in client
        '''
        return self.client_property_getter_connection('host_connection')

    @host_connection.setter
    def host_connection(self, value):
        '''
        Set the *value* as current host_connection id in client
        '''
        self.client_property_setter_connection('host_connection', value)

    @property
    def host_connections(self):
        '''
        Available host_connections in client
        '''
        return self.client_property_getter_connection('host_connections')

    # TODO: evaluate if used and if needed
    @property
    def plugins(self):
        '''
        Available plugins in the current tool_config
        '''
        if not self.tool_config:
            self.logger.warning(
                "Please set a tool_config before quering plugins"
            )
            return None
        return self.tool_config.get_all(category='plugin')

    @property
    def framework_widgets(self):
        '''Return initialized framework widgets'''
        return self.__framework_widget_registry

    @property
    def discovered_framework_widgets(self):
        '''Return discovered framework widgets from client'''
        return self.client_property_getter_connection(
            'discovered_framework_widgets'
        )

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
        # Set properties to 0
        self._tool_configs = None
        self._host_connections = None
        self._tool_config = None
        self._host_connection = None
        self.__framework_widget_registry = {}

        # Connect client methods and properties
        self.connect_methods(connect_methods_callback)
        self.connect_properties(
            connect_setter_property_callback, connect_getter_property_callback
        )
        # TODO: implement dialog_options
        self._dialog_options = dialog_options

        super(FrameworkDialog, self).__init__(event_manager, client_id, parent)

    def connect_methods(self, method):
        '''
        Connect the client callback method for the dialog to be able to execute
        client methods.
        '''
        self.client_method_connection = method

    def connect_properties(self, set_method, get_method):
        '''
        Connect the client setter and getter properties for the dialog to be
        able to call them.
        '''
        self.client_property_setter_connection = set_method
        self.client_property_getter_connection = get_method

    def _subscribe_client_events(self):
        '''Subscribe to all client events and signals'''
        self.event_manager.subscribe.client_signal_context_changed(
            self.client_id, callback=self._on_client_context_changed_callback
        )
        self.event_manager.subscribe.client_signal_hosts_discovered(
            self.client_id, callback=self._on_client_hosts_discovered_callback
        )
        self.event_manager.subscribe.client_signal_host_changed(
            self.client_id, callback=self._on_client_host_changed_callback
        )
        self.event_manager.subscribe.client_notify_run_plugin_result(
            self.client_id,
            callback=self._on_client_notify_ui_run_plugin_result_callback,
        )
        self.event_manager.subscribe.client_notify_run_tool_config_result(
            self.client_id,
            callback=self._on_client_notify_ui_run_tool_config_result_callback,
        )
        self.event_manager.subscribe.client_notify_log_item_added(
            self.client_id,
            callback=self._on_client_notify_ui_log_item_added_callback,
        )

    def show_ui(self):
        '''
        To be overriden by the implemented dialog. Should execute the dialog:
        Pseudocode example PySide UI:
        self.show()
        '''
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    def connect_focus_signal(self):
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    @active_widget
    def _on_client_context_changed_callback(self, event=None):
        '''
        Will only run if the widget is active
        Callback for when context has changed in client.
        '''
        for id, widget in self.framework_widgets.items():
            widget.update_context(self.context_id)

    @active_widget
    def _on_client_hosts_discovered_callback(self, event=None):
        '''
        Will only run if the widget is active
        Callback for when new host has been discovered in client.
        '''
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    @active_widget
    def _on_client_host_changed_callback(self, event=None):
        '''
        Will only run if the widget is active
        Callback for when host has changed in the client.
        '''
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    @active_widget
    def _on_tool_config_changed_callback(self):
        '''
        Callback for when tool_config has changed.
        '''
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    def _on_focus_changed(self, old_widget, new_widget):
        '''
        Set the *new_widget* as active and synchronize the context, host and
        tool config with the client.
        '''
        # TODO: evaluate if this should be implemented in the widget
        if self == old_widget:
            self.is_active = False
        elif self == new_widget:
            self.is_active = True
        else:
            self.is_active = False
        if self.is_active:
            # Synchronize context with client
            self.sync_context()
            # Synchronize Host connection with client
            self.sync_host_connection()

    def sync_context(self):
        '''
        Check if selected UI context_id is not sync with the client and sync them.
        Pseudocode example PySide UI:
        if self.context_id not is self.context_Selector.current_text():
            raise confirmation widget to decide which one to keep
            equal self.context_Selector.current_text() to self.context_id or
            the other way around depending on the confirmation widget response
        '''
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    def sync_host_connection(self):
        '''
        Check if UI selected host_connection is not sync with the client and sync them.
        '''
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    def init_framework_widget(self, plugin_config):
        '''
        Method to initialize a framework widget given in the *plugin_config*
        '''
        widget_class = None
        for widget in self.discovered_framework_widgets:
            if widget.name == plugin_config.widget_name:
                widget_class = widget
                break
        if not widget_class:
            error_message = (
                'The provided widget {} for plugin {} is not registered '
                'Please provide a registered widget.\n '
                'Registered widgets: {}'.format(
                    plugin_config.widget_name,
                    plugin_config.plugin_name,
                    self.discovered_framework_widgets,
                )
            )
            self.logger.error(error_message)
            raise Exception(error_message)
        widget = widget_class(
            self.event_manager,
            self.client_id,
            self.context_id,
            plugin_config,
            dialog_connect_methods_callback=self._connect_dialog_methods_callback,
            dialog_property_getter_connection_callback=self._connect_dialog_property_getter_connection_callback,
        )
        self._register_widget(widget)
        return widget

    def _register_widget(self, widget):
        '''
        Registers the initialized *widget* to the dialog registry.
        '''
        if widget.id not in list(self.__framework_widget_registry.keys()):
            self.__framework_widget_registry[widget.id] = widget

    def _connect_dialog_methods_callback(
        self, method_name, arguments=None, callback=None
    ):
        '''Enables widgets call dialog methods'''
        meth = getattr(self, method_name)
        if not arguments:
            arguments = {}
        result = meth(**arguments)
        # Callback might not be available if its is an async method like run_plugin
        if callback:
            callback(result)
        return result

    def _connect_dialog_property_getter_connection_callback(
        self, property_name
    ):
        '''Enables widgets to call dialog properties'''
        return self.__getattribute__(property_name)

    def run_plugin_method(
        self, plugin_config, plugin_method_name, plugin_widget_id=None
    ):
        '''
        Dialog tell client to run the *plugin_method_name* from the
        *plugin_config* .
        Provides a *plugin_widget_id* if its a widget who wants to execute the
        method.
        '''
        # No callback as it is returned by an event
        arguments = {
            "plugin_config": plugin_config,
            "plugin_method_name": plugin_method_name,
            "engine_type": self.tool_config.engine_type,
            "engine_name": self.tool_config.engine_name,
            'plugin_widget_id': plugin_widget_id,
        }
        self.client_method_connection('run_plugin', arguments=arguments)

    def _on_client_notify_ui_run_plugin_result_callback(self, event):
        '''
        Client has notified the dialog about a result of a plugin method,
        now the dialog notifies the widget that has executed the method.
        '''
        plugin_info = event['data']['plugin_info']
        plugin_widget_id = plugin_info['plugin_widget_id']
        widget = self.framework_widgets.get(plugin_widget_id)
        widget.run_plugin_callback(plugin_info)

    def _on_client_notify_ui_run_tool_config_result_callback(self, event):
        '''
        Client notifies the dialog that tool_config has been executed and passes
        the result in the *event*
        '''
        tool_config_result = event['data']['tool_config_result']
        # TODO: do something with the result

    def _on_client_notify_ui_log_item_added_callback(self, event):
        '''
        Client notifiies dialog that a new log item has been added.
        '''
        log_item = event['data']['log_item']
        # TODO: do something with the log_item
