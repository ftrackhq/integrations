# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import uuid
from functools import partial

from ftrack_framework_core.widget import BaseUI, active_widget
from ftrack_utils.framework.config.tool import (
    get_tool_config_by_name,
    get_plugins,
)


class FrameworkDialog(BaseUI):
    '''
    Base Class to represent a FrameworkDialog, all the dialogs executed by the
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
        tool_configs = {}
        for tool_config_type in self.tool_config_type_filter:
            tool_configs[tool_config_type] = self.tool_configs.get(
                tool_config_type
            )
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

        if value and not get_tool_config_by_name(
            self.tool_configs[value['config_type']], value['name']
        ):
            self.logger.error(
                "Invalid tool_config, choose one from : {}".format(
                    self.tool_configs
                )
            )
            return

        if value:
            # Get plugins from tool_config
            plugins = get_plugins(value, names_only=True)

            unregistered_plugins = self.client_method_connection(
                'verify_plugins', arguments={"plugin_names": plugins}
            )
            if unregistered_plugins:
                raise Exception(
                    f"Unregistered plugins found: {unregistered_plugins}"
                    f"\n Please make sure plugins are in the extensions path"
                )

        self._tool_config = value

        if self._tool_config:
            arguments = {
                "tool_config_reference": self._tool_config['reference'],
                "item_reference": None,
                "options": self.dialog_options,
            }
            self.client_method_connection(
                'set_config_options', arguments=arguments
            )

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

    @property
    def framework_widgets(self):
        '''Return instanced framework widgets'''
        return self.__instanced_widgets

    @property
    def registry(self):
        '''Return discovered framework widgets from client'''
        return self.client_property_getter_connection('registry')

    @property
    def tool_config_options(self):
        '''
        Current tool_config_options in client
        '''
        return self.client_property_getter_connection('tool_config_options')

    @property
    def dialog_options(self):
        '''Return dialog options as passed on from client'''
        return self._dialog_options or {}

    @property
    def id(self):
        '''
        Id of the plugin
        '''
        return self._id

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
        self.__instanced_widgets = {}
        self._id = uuid.uuid4().hex
        self._client_signal_context_changed_subscribe_id = None
        self._client_notify_log_item_added_subscribe_id = None
        self._client_notify_ui_hook_result_subscribe_id = None

        # Connect client methods and properties
        self.connect_methods(connect_methods_callback)
        self.connect_properties(
            connect_setter_property_callback, connect_getter_property_callback
        )
        self._dialog_options = dialog_options

        super(FrameworkDialog, self).__init__(
            event_manager, client_id, parent=parent
        )

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

        self._client_signal_context_changed_subscribe_id = (
            self.event_manager.subscribe.client_signal_context_changed(
                self.client_id,
                callback=self._on_client_context_changed_callback,
            )
        )
        self._client_notify_log_item_added_subscribe_id = (
            self.event_manager.subscribe.client_notify_log_item_added(
                self.client_id,
                callback=self._on_client_notify_ui_log_item_added_callback,
            )
        )
        self._client_notify_ui_hook_result_subscribe_id = (
            self.event_manager.subscribe.client_notify_ui_hook_result(
                self.client_id,
                callback=self._on_client_notify_ui_hook_result_callback,
            )
        )

    def _unsubscribe_client_events(self):
        '''Unsubscribe to all client events and signals'''
        if self._client_signal_context_changed_subscribe_id:
            self.event_manager.unsubscribe(
                self._client_signal_context_changed_subscribe_id
            )
            self._client_signal_context_changed_subscribe_id = None
        if self._client_notify_log_item_added_subscribe_id:
            self.event_manager.unsubscribe(
                self._client_notify_log_item_added_subscribe_id
            )
            self._client_notify_log_item_added_subscribe_id = None
        if self._client_notify_ui_hook_result_subscribe_id:
            self.event_manager.unsubscribe(
                self._client_notify_ui_hook_result_subscribe_id
            )
            self._client_notify_ui_hook_result_subscribe_id = None

    def show_ui(self):
        '''
        To be overriden by the implemented dialog. Should execute the dialog:
        Pseudocode example PySide UI:
        self.show()
        '''
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    def ui_closed(self):
        '''Should be called by the inheriting class when the dialog is closed'''
        self._unsubscribe_client_events()

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
            # Synchronize Host connection with client
            self.sync_host_connection()
            # Synchronize context with client
            self.sync_context()

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

    def init_framework_widget(self, plugin_config, group_config=None):
        '''
        Method to initialize a framework widget given in the *plugin_config*.
        *group_config* as optional argument in case is part of a group.
        '''
        widget_class = None
        for widget in self.registry.widgets:
            if widget['name'] == plugin_config['ui']:
                widget_class = widget['extension']
                break
        if not widget_class:
            error_message = (
                'The provided widget {} for plugin {} is not registered '
                'Please provide a registered widget.\n '
                'Registered widgets: {}'.format(
                    plugin_config['ui'],
                    plugin_config['plugin'],
                    self.registry.widgets,
                )
            )
            self.logger.error(error_message)
            raise Exception(error_message)
        try:
            widget = widget_class(
                self.event_manager,
                self.client_id,
                self.context_id,
                plugin_config,
                group_config,
                on_set_plugin_option=partial(
                    self._on_set_plugin_option_callback,
                    plugin_config['reference'],
                ),
                on_run_ui_hook=partial(
                    self._on_run_ui_hook_callback, plugin_config['reference']
                ),
            )
        except:
            # Log the exception and raise it
            self.logger.exception(
                msg='Error while loading widget : {}'.format(widget_class)
            )
            raise
        # TODO: widgets can't really run any plugin (like fetch) before it gets
        #  registered, so In case someone automatically fetches during the init
        #  of the widget it will fail because its not registered yet. Task is to
        #  find a way to better handle the registry.
        self._register_widget(plugin_config['reference'], widget)
        # Just a quick hack to test query assets
        widget.populate()
        return widget

    def _register_widget(self, plugin_reference, widget):
        '''
        Registers the initialized *widget* to the dialog registry.
        '''
        if plugin_reference not in list(self.__instanced_widgets.keys()):
            self.__instanced_widgets[plugin_reference] = widget

    def unregister_widget(self, widget_name):
        '''
        Remove the given *widget_name* from the registered widgets.
        '''
        for plugin_reference, widget in self.framework_widgets.items():
            if widget_name == widget.name:
                self.__instanced_widgets.pop(plugin_reference)
                self.logger.info(
                    "Unregistering widget: {}".format(widget_name)
                )
                break

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

    def run_tool_config(self, tool_config_reference):
        '''
        Run button from the UI has been clicked.
        Tell client to run the current tool config
        '''

        arguments = {"tool_config_reference": tool_config_reference}
        self.client_method_connection('run_tool_config', arguments=arguments)

    def _on_client_notify_ui_log_item_added_callback(self, event):
        '''
        Client notify dialog that a new log item has been added.
        '''
        log_item = event['data']['log_item']
        self.plugin_run_callback(log_item)
        reference = log_item.reference
        if not reference:
            return
        widget = self.framework_widgets.get(reference)
        if not widget:
            self.logger.warning(
                "Widget with reference {} can't be found on the dialog "
                "initialized widgets".format(reference)
            )
            return
        widget.plugin_run_callback(log_item)

    def plugin_run_callback(self, log_item):
        '''
        Dialog to receive the callback with the plugin info every time a plugin has been
        executed. To be overridden by the inheriting class.
        *log_item* is the plugin info dictionary.
        '''
        pass

    def _on_client_notify_ui_hook_result_callback(self, event):
        '''
        Client notify ui with the result of running the UI hook.
        '''
        reference = event['data']['plugin_reference']
        ui_hook_result = event['data']['ui_hook_result']

        if not reference:
            return
        widget = self.framework_widgets.get(reference)
        if not widget:
            self.logger.warning(
                "Widget with reference {} can't be found on the dialog "
                "initialized widgets".format(reference)
            )
            return
        widget.ui_hook_callback(ui_hook_result)

    def _on_set_plugin_option_callback(self, plugin_reference, options):
        '''
        Pass the given *options* of the *plugin_reference* to the client.
        '''
        self.set_tool_config_option(options, plugin_reference)

    def set_tool_config_option(self, options, item_reference=None):
        '''
        Set the given name and value as options for the current tool config.
        '''
        arguments = {
            "tool_config_reference": self.tool_config['reference'],
            "options": options,
        }
        if item_reference:
            arguments['item_reference'] = item_reference
        self.set_option_callback(arguments)

    def set_option_callback(self, args):
        '''
        Pass the given *args* to the client set_config_options method.
        '''
        self.client_method_connection('set_config_options', arguments=args)

    def _on_run_ui_hook_callback(self, plugin_reference, payload):
        arguments = {
            "tool_config_reference": self.tool_config['reference'],
            "plugin_config_reference": plugin_reference,
            "payload": payload,
        }
        self.client_method_connection('run_ui_hook', arguments=arguments)

    @classmethod
    def register(cls):
        '''
        Register function to discover widget by class *cls*. Returns False if the
        class is not registrable.
        '''
        import inspect

        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )
        logger.debug(
            'registering: {} for {}'.format(cls.name, cls.widget_type)
        )

        if not hasattr(cls, 'name') or not cls.name:
            # Can only register widgets that have a name, not base classes
            logger.warning(
                "Can only register dialogs that have a name, no name provided "
                "for this one"
            )
            return False

        data = {
            'extension_type': 'dialog',
            'name': cls.name,
            'extension': cls,
            'path': inspect.getfile(cls),
        }

        return data
