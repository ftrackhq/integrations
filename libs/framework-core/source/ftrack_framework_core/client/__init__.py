# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import time
import logging
import uuid
from collections import defaultdict

from six import string_types

from ftrack_framework_widget.dialog import FrameworkDialog
import ftrack_constants.framework as constants

from ftrack_framework_core.client.host_connection import HostConnection


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
        if not self.host_connection:
            self.logger.warning('No host connection available')
            return
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

    # TODO: double check how we enable disable multithreading,
    #  I think we can improve it and make it simpler, take a look at the
    #  active_ui decorator that I created, maybe we can use something similar.
    @property
    def multithreading_enabled(self):
        '''Return True if client supports multithreading (write operations)'''
        return self._multithreading_enabled

    # Widget
    @property
    def dialogs(self):
        '''Return instanced dialogs'''
        return self.__instanced_dialogs

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
    def discovered_widgets(self):
        '''Return discovered framework widgets'''
        return self.__widgets_discovered

    @property
    def discovered_dialogs(self):
        '''Return discovered framework widgets'''
        return self.__dialogs_discovered

    @property
    def tool_config_options(self):
        return self._tool_config_options

    def __init__(
        self,
        event_manager,
        registry,
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

        # Create the client id to use to communicate with UI
        self._id = '{}'.format(uuid.uuid4().hex)

        # Set the event manager
        self._event_manager = event_manager

        # Set multithreading
        self._multithreading_enabled = multithreading_enabled

        # Setting init variables to 0
        self._host_context_changed_subscribe_id = None
        self.__widgets_discovered = []
        self.__dialogs_discovered = []
        self.__instanced_dialogs = {}
        self._dialog = None
        self._auto_connect_host = auto_connect_host
        self._tool_config_options = defaultdict(defaultdict)

        # Register modules
        self._register_modules(registry)

        self.logger.debug('Initialising Client {}'.format(self))

        if auto_discover_host and not self.host_connections:
            self.discover_hosts()

    def _register_modules(self, registry):
        '''
        Register framework modules available.
        '''
        # Discover widget modules
        self.discover_dialogs(registry.dialogs)
        # Discover widget modules
        self.discover_widgets(registry.widgets)

        if self.__widgets_discovered and self.__dialogs_discovered:
            # Check that registry went correct
            return True
        self.logger.warning('No dialogs or widgets found to register')

    def discover_widgets(self, registered_widgets):
        '''
        Register the given *registered_widgets* on the
        :obj:`self.__widgets_discovered`
        '''
        self.__widgets_discovered = registered_widgets

    def discover_dialogs(self, registered_dialogs):
        '''
        Register the given *registered_dialogs* on the
        :obj:`self.__dialogs_discovered`
        '''
        self.__dialogs_discovered = registered_dialogs

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

    def on_host_changed(self, host_connection):
        '''Called when the host has been (re-)selected by the user.'''
        # Emit signal to widget
        self.event_manager.publish.client_signal_host_changed(self.id)

    # Context
    def _host_context_changed_callback(self, event):
        '''Set the new context ID based on data provided in *event*'''
        # Feed the new context to the client
        self.on_context_changed(event['data']['context_id'])

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
    def run_tool_config(self, tool_config_reference):
        '''
        Publish event to tell the host to run the given *tool_config_reference*
        on the engine.
        *tool_config_reference*: id number of the tool config.
        '''
        self.event_manager.publish.host_run_tool_config(
            self.host_id,
            tool_config_reference,
            self.tool_config_options.get(tool_config_reference, {}),
        )

    # Plugin
    def on_log_item_added_callback(self, event):
        '''
        Called when a log item has added in the host.
        '''
        log_item = event['data']['log_item']
        self.logger.info(
            "Plugin Execution progress: \n "
            "plugin_name: {} \n"
            "plugin_status: {} \n"
            "plugin_message: {} \n"
            "plugin_execution_time: {} \n"
            "plugin_store: {} \n".format(
                log_item.plugin_name,
                log_item.plugin_status,
                log_item.plugin_message,
                log_item.plugin_execution_time,
                log_item.plugin_options,
                log_item.plugin_store,
            )
        )
        # Publish event to widget
        self.event_manager.publish.client_notify_log_item_added(
            self.id, event['data']['log_item']
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

            if dialog_class not in [
                dialog['extension'] for dialog in self.discovered_dialogs
            ]:
                self.logger.warning(
                    'Provided dialog_class {} not in the discovered framework '
                    'widgets, registering...'.format(dialog_class)
                )
                self.__dialogs_discovered.append(
                    {
                        'extension_type': 'dialog',
                        'name': dialog_name,
                        'extension': dialog_class,
                    }
                )

        if dialog_name and not dialog_class:
            for registered_dialog_class in self.discovered_dialogs:
                if dialog_name == registered_dialog_class['name']:
                    dialog_class = registered_dialog_class['extension']
                    break
        if not dialog_class:
            error_message = (
                'Please provide a registered dialog name.\n'
                'Given name: {} \n'
                'registered widgets: {}'.format(
                    dialog_name, self.discovered_dialogs
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
        self.dialog.setFocus()

    def _register_dialog(self, dialog):
        '''Register the given initialized *dialog* to the dialogs registry'''
        if dialog.id not in list(self.__instanced_dialogs.keys()):
            self.__instanced_dialogs[dialog.id] = dialog

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

    def set_config_options(
        self, tool_config_reference, plugin_config_reference, plugin_options
    ):
        if not isinstance(plugin_options, dict):
            raise Exception(
                "plugin_options should be a dictionary. "
                "Current given type: {}".format(plugin_options)
            )
        self._tool_config_options[tool_config_reference][
            plugin_config_reference
        ] = plugin_options
