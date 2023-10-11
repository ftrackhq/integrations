# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import time
import logging
import uuid

from six import string_types

from ftrack_utils.framework.dependencies import registry
from ftrack_framework_widget.dialog import FrameworkDialog
import ftrack_constants.framework as constants

from ftrack_framework_core.client.host_connection import HostConnection

# TODO: implement ABC


class Client(object):
    '''
    Base client class.
    '''

    # tODO: evaluate if to use compatible UI types in here or directly add the list of ui types
    ui_types = constants.client.COMPATIBLE_UI_TYPES
    '''Compatible UI for this client.'''

    # TODO: Double check with the team if this is needed to have a singleton host
    #  connection and if it still makes sense to be a singleton as we only have
    #  one client now.
    _host_connection = None
    '''The singleton host connection used by all clients within the process space / DCC'''
    _host_connections = []
    '''The list of discovered host connections'''

    def __repr__(self):
        return '<Client:{0}>'.format(self.id)

    @property
    def id(self):
        '''Returns the current client id.'''
        return self._id

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`'''
        return self._event_manager

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    # TODO: Discuss if we want to change name to available_hosts
    @property
    def host_connections(self):
        '''Return the current list of host_connections'''
        return Client._host_connections

    @host_connections.setter
    def host_connections(self, value):
        '''Return the current list of host_connections'''
        Client._host_connections = value

    # TODO: Discuss if we want to change this to connected host
    @property
    def host_connection(self):
        '''
        Return instance of
        :class:`~ftrack_framework_core.client.HostConnection`
        '''
        return Client._host_connection

    @host_connection.setter
    def host_connection(self, value):
        '''
        Assign the host_connection to the given *value*

        *value* : should be instance of
        :class:`~ftrack_framework_core.client.HostConnection`
        '''
        if not value:
            # Clean up host_context_change_subscription in case exists
            self._unsubscribe_host_context_changed()
            Client._host_connection = value
            self.on_host_changed(self.host_connection)
            return
        if (
            self.host_connection
            and value.host_id == self.host_connection.host_id
        ):
            return

        self.logger.debug('Setting new host connection: {}'.format(value))
        Client._host_connection = value

        # Subscribe log item added
        self.event_manager.subscribe.host_log_item_added(
            self.host_connection.host_id,
            callback=self.on_log_item_added_callback,
        )
        # Clean up host_context_change_subscription in case exists
        self._unsubscribe_host_context_changed()
        # Subscribe to host_context_change even though we already subscribed in
        # the host_connection. This is because we want to let the client know
        # that host changed context but also update the host connection to the
        # new context.
        self._host_context_changed_subscribe_id = (
            self.event_manager.subscribe.host_context_changed(
                self.host_connection.host_id,
                self._host_context_changed_callback,
            )
        )
        # Feed change of host and context to client
        self.on_host_changed(self.host_connection)
        self.on_context_changed(self.host_connection.context_id)

    @property
    def host_id(self):
        '''returns the host id from the current host connection'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        return self.host_connection.host_id

    @property
    def context_id(self):
        '''Returns the current context id from current host connection'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        return self.host_connection.context_id

    @context_id.setter
    def context_id(self, context_id):
        '''Publish the given *context_id to be set by the host'''
        if not isinstance(context_id, string_types):
            raise ValueError('Context should be in form of a string.')
        if self.host_connection is None:
            raise Exception('No host connection available')
        # Publish event to notify host that client has changed the context
        self.event_manager.publish.client_context_changed(
            self.host_id, context_id
        )

    @property
    def host_context_changed_subscribe_id(self):
        '''The subscription id of the host context changed event'''
        return self._host_context_changed_subscribe_id

    @property
    def tool_configs(self):
        '''Returns all available tool_configs from the current host_ connection'''
        if not self.host_connection:
            raise Exception('No host connection available')
        return self.host_connection.tool_configs

    # TODO: double check how we enable disbale multithreading,
    #  I think we can improve it and make it simpler, take a look at the
    #  active_ui decorator that I created, maybe we can use soemthing similar.
    @property
    def multithreading_enabled(self):
        '''Return True if client supports multithreading (write operations)'''
        return self._multithreading_enabled

    # Widget
    @property
    def dialogs(self):
        '''Return Initalized dialogs'''
        return self.__dialogs_registry

    @property
    def dialog(self):
        '''Return the current active dialog'''
        return self._dialog

    @dialog.setter
    def dialog(self, value):
        # TODO: Check value is type of framework dialog
        '''Set the given *value* as the current active dialog'''
        self.set_active_dialog(self._dialog, value)
        self._dialog = value

    @property
    def discovered_framework_widgets(self):
        '''Return discovered framework widgets'''
        return self.__framework_widget_registry

    def __init__(
        self,
        event_manager,
        auto_discover_host=True,
        auto_connect_host=True,
        multithreading_enabled=True,
    ):
        '''
        Initialise Client with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        # TODO: double check logger initialization and standardize it around all files.
        # Setting logger
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # Create the client id to use to comunicate with UI
        self._id = '{}'.format(uuid.uuid4().hex)

        # Set the event manager
        self._event_manager = event_manager

        # Set multithreading
        self._multithreading_enabled = multithreading_enabled

        # Setting init variables to 0
        self._host_context_changed_subscribe_id = None
        self.__framework_widget_registry = []
        self.__dialogs_registry = {}
        self._dialog = None
        self._auto_connect_host = auto_connect_host

        # Register modules
        self._register_modules()

        self.logger.debug('Initialising Client {}'.format(self))

        if auto_discover_host and not self.host_connections:
            self.discover_hosts()

    def _register_modules(self):
        '''
        Register framework modules available.
        '''
        # We register the plugins first so they can subscribe to the discover event
        registry.register_framework_modules_by_type(
            event_manager=self.event_manager,
            module_type='widgets',
            callback=self._on_register_framework_widgets_callback,
        )

        if self.__framework_widget_registry:
            # Check that registry went correct
            return True
        self.logger.warning('No widgets found to register')

    def _on_register_framework_widgets_callback(self, registered_widgets):
        '''
        Callback of the :meth:`_register_framework_modules` of type plugins.
        We add all the *registered_plugins* into our
        :obj:`self.__plugins_registry`
        '''

        discovered_widgets = []
        registered_widgets = list(set(registered_widgets))
        for widget in registered_widgets:
            # TODO: to support self.ui_types in the event manager we have to ask
            #  for a python API modification in the backend to support the
            #  operator "in" for lists

            result = None
            for ui_type in self.ui_types:
                result = self.event_manager.publish.discover_widget(
                    ui_type,
                    widget.name,
                )
                if result:
                    discovered_widgets.append(widget)
                    break
            if not result:
                self.logger.warning(
                    " The widget {} hasn't been registered. "
                    "Check compatible UI types: {}".format(
                        widget.name, self.ui_types
                    )
                )

        self.__framework_widget_registry = discovered_widgets

    # Host
    def discover_hosts(self, time_out=3):
        '''
        Find for available hosts during the optional *time_out*.

        This removes all previously discovered host connections.
        '''
        # Reset host connections
        self.host_connections = []
        if self.host_connection:
            self._unsubscribe_host_context_changed()
            self.host_connection = None

        # discovery host loop and timeout.
        start_time = time.time()
        self.logger.debug('time out set to {}:'.format(time_out))
        if not time_out:
            self.logger.warning(
                'Running client with no time out.'
                'Will not stop until discover a host.'
                'Terminate with: Ctrl-C'
            )

        while not self.host_connections:
            delta_time = time.time() - start_time

            if time_out and delta_time >= time_out:
                self.logger.warning('Could not discover any host.')
                break

            self.event_manager.publish.discover_host(
                callback=self._host_discovered_callback
            )

        # Feed host connections to the client
        self.on_hosts_discovered(self.host_connections)

    def _host_discovered_callback(self, event):
        '''
        Reply callback of the discover host event, generate
        :class:`~ftrack_framework_core.client.HostConnection`
        of all discovered hosts from the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        if not event['data']:
            return
        for reply_data in event['data']:
            host_connection = HostConnection(self.event_manager, reply_data)
            if (
                host_connection
                and host_connection not in self.host_connections
            ):
                self.host_connections.append(host_connection)

    def on_hosts_discovered(self, host_connections):
        '''
        Callback, hosts has been discovered.
        Widgets can hook in the published signal.
        '''
        if self._auto_connect_host:
            # Automatically connect to the first one
            self.host_connection = host_connections[0]
        # Emit signal to widget
        self.event_manager.publish.client_signal_hosts_discovered(self.id)

    # TODO: this should be ABC method
    def on_host_changed(self, host_connection):
        '''Called when the host has been (re-)selected by the user.'''
        # Emit signal to widget
        self.event_manager.publish.client_signal_host_changed(self.id)

    # Context
    def _host_context_changed_callback(self, event):
        '''Set the new context ID based on data provided in *event*'''
        # Feed the new context to the client
        self.on_context_changed(event['data']['context_id'])

    # TODO: this should be ABC method
    def on_context_changed(self, context_id):
        '''Called when the context has been set or changed within the
        host connection, either from this client or remote
        (other client or the host).
        '''
        # Emit signal to widget
        self.event_manager.publish.client_signal_context_changed(self.id)

    def _unsubscribe_host_context_changed(self):
        '''Unsubscribe to client context change events'''
        if self.host_context_changed_subscribe_id:
            self.session.event_hub.unsubscribe(
                self.host_context_changed_subscribe_id
            )
            self._host_context_changed_subscribe_id = None

    # Tool config
    def run_tool_config(self, tool_config):
        '''
        Publish event to tell the host to run the given *tool_config* with the
        given *engine*.
        '''
        self.event_manager.publish.host_run_tool_config(
            self.host_id,
            tool_config.to_dict(),
            self._run_tool_config_callback,
        )

    # TODO: this should be ABC method
    def _run_tool_config_callback(self, event):
        '''Callback of the :meth:`~ftrack_framework_core.client.run_tool_config'''
        self.logger.debug("_run_tool_config_callback event: {}".format(event))
        result = event['data']
        if type(event['data']) == list():
            result = event['data'][0]
        # Publish event to widget
        self.event_manager.publish.client_notify_run_tool_config_result(
            self.id, event['data']
        )

    # Plugin
    def run_plugin(
        self,
        plugin_config,
        plugin_method_name,
        engine_type,
        engine_name,
        plugin_widget_id=None,
    ):
        '''
        Publish event to tell the host to run the given *plugin_method_name*
        of the *plugin_config* with the given *engine*.

        Result of the executed plugin method specified in the
        *plugin_config* will be passed to
        :meth:`~ftrack_framework_core.client._run_plugin_callback`.
        '''

        self.event_manager.publish.host_run_plugin(
            self.host_id,
            plugin_config,
            plugin_method_name,
            engine_type,
            engine_name,
            plugin_widget_id,
            self._run_plugin_callback,
        )

    #  converted to ABC method.
    def _run_plugin_callback(self, event):
        '''
        Callback of the :meth:`~ftrack_framework_core.client.run_plugin
        This method publish the client_notify_run_plugin_result.
        As example, this event is subscribed by the FrameworkDialog so this can
        get the results.
        '''
        self.logger.debug("_run_plugin_callback event: {}".format(event))
        # Publish event to widget
        self.event_manager.publish.client_notify_run_plugin_result(
            self.id, event['data'][0]
        )

    def on_log_item_added_callback(self, event):
        '''
        Called when a log item has added in the host.
        '''
        log_item = event['data']['log_item']
        self.logger.info(
            "Plugin Execution progress: \n "
            "plugin_name: {} \n"
            "plugin_type: {} \n"
            "plugin_status: {} \n"
            "plugin_message: {} \n"
            "plugin_method: {} \n"
            "plugin_method_result: {} \n"
            "plugin_context_data: {} \n"
            "plugin_data: {} \n"
            "plugin_options: {} \n".format(
                log_item.plugin_name,
                log_item.plugin_type,
                log_item.plugin_status,
                log_item.plugin_message,
                log_item.plugin_method,
                log_item.plugin_method_result,
                log_item.plugin_context_data,
                log_item.plugin_data,
                log_item.plugin_options,
            )
        )
        # Publish event to widget
        self.event_manager.publish.client_notify_log_item_added(
            self.id, event['data']['log_item']
        )

    def reset_tool_config(self, tool_config_name, tool_config_type):
        '''
        Ask host connection to reset values of a specific tool_config
        '''
        self.host_connection.reset_tool_config(
            tool_config_name, tool_config_type
        )

    def reset_all_tool_configs(self):
        '''
        Ask host connection to reset values of all tool_configs
        '''
        self.host_connection.reset_all_tool_configs()

    # UI
    def run_dialog(self, dialog_name, dialog_class=None, dialog_options=None):
        '''Function to show a framework dialog from the client'''
        # use dialog options to pass options to the dialog like for
        #  example: Dialog= WidgetDialog dialog_options= {tool_config_plugin: Context_selector}
        #  ---> So this will execute the widget dialog with the widget of the
        #  context_selector in it, it simulates a run_widget).
        #  Or any other kind of option like docked or not

        if dialog_class:
            if not isinstance(dialog_class, FrameworkDialog):
                error_message = (
                    'The provided class {} is not instance of the base framework '
                    'widget. Please provide a supported widget.'.format(
                        dialog_class
                    )
                )
                self.logger.error(error_message)
                raise Exception(error_message)

            if dialog_class not in self.discovered_framework_widgets:
                self.logger.warning(
                    'Provided dialog_class {} not in the discovered framework '
                    'widgets, registering...'.format(dialog_class)
                )
                self.__framework_widget_registry.append(dialog_class)

        if dialog_name and not dialog_class:
            for registered_dialog_class in self.discovered_framework_widgets:
                if dialog_name == registered_dialog_class.name:
                    dialog_class = registered_dialog_class
                    break
        if not dialog_class:
            error_message = (
                'Please provide a registrated dialog name.\n'
                'Given name: {} \n'
                'registered widgets: {}'.format(
                    dialog_name, self.discovered_framework_widgets
                )
            )
            self.logger.error(error_message)
            raise Exception(error_message)

        dialog = dialog_class(
            self.event_manager,
            self.id,
            connect_methods_callback=self._connect_methods_callback,
            connect_setter_property_callback=self._connect_setter_property_callback,
            connect_getter_property_callback=self._connect_getter_property_callback,
            dialog_options=dialog_options,
        )
        # Append dialog to dialogs
        self._register_dialog(dialog)
        self.dialog = dialog
        self.dialog.show_ui()

    def _register_dialog(self, dialog):
        '''Register the given initialized *dialog* to the dialogs registry'''
        if dialog.id not in list(self.__dialogs_registry.keys()):
            self.__dialogs_registry[dialog.id] = dialog

    def set_active_dialog(self, old_dialog, new_dialog):
        '''Remove focus from the *old_dialog* and set the *new_dialog*'''
        for dialog in list(self.dialogs.values()):
            dialog.change_focus(old_dialog, new_dialog)

    def _connect_methods_callback(
        self, method_name, arguments=None, callback=None
    ):
        '''
        Callback from the dialog to execute the given *method_name* from the
        client with the given *arguments* call the given *callback* once we have
        the result
        '''
        meth = getattr(self, method_name)
        if not arguments:
            arguments = {}
        result = meth(**arguments)
        if callback:
            callback(result)
        return result

    def _connect_setter_property_callback(self, property_name, value):
        '''
        Callback from the dialog, set the given *property_name* from the
        client to the given *value*
        '''
        self.__setattr__(property_name, value)

    def _connect_getter_property_callback(self, property_name):
        '''
        Callback from the dialog, return the value of the given *property_name*
        '''
        return self.__getattribute__(property_name)
