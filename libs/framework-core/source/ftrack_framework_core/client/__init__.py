# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import time
import logging
import uuid

from six import string_types

from ftrack_framework_core.client.host_connection import HostConnection
from ftrack_framework_core import constants

# TODO: add a dicover_uis widget and dialgos method.

# TODO: has a discussion on how client should communicate to widget.
#  Example just via events:
#       UI publish --> run_method (method_name, arguments, callback) --> Client subscribes
#       UI publish --> set_method (property_name, value) --> Client subscribes
#       Client publish --> log_item_added (log_item) --> UI subscribes
#       Client publish --> host_connection_added (host_conections) --> UI subscribes
#       Client publish --> definition_set (definition) --> UI subscribes
#       ### PROBLEM ###
#       UI problem: Now the UI has the definition that is set, but the definition
#       is just a raw json and not a DefinitionObject, so to deal with finding
#       all the plugins and augment the options will be very complicated.
#       ### Possible solutions ###
#       1: We split DefinitionObject from framework_core so booth ftrack_qt and
#       ftrack_core can have it as dependnency, then once defiition_set event
#       arrives to the UI we convert the definition to a DefinitionObject
#       2: We connect with direct connection using the current methods. So UI is
#       like an extension of the client. It is allways reading definitions directly
#       from client and overriding them directly in the client. Also we use some
#       events per convinience, like log_item_added, notify_progress_to_ui, etc...
#       In this case, I have one more question:
#           Should the UI subscribe to the host events directly or they should
#           only be subscribed by the client?
#           I think the second sceneario is safer because the client proceeds
#           the data as we want, and then publish a new event to be picked by the UI.
#           So this way we ensure that the UI always receives data that has been
#           handled by th client first.

class Client(object):
    '''
    Base client class.
    '''

    # TODO: do we need to specify ui compatible types?
    ui_types = [constants.UI_TYPE]
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

    # TODO: I think there should be a midle man that is a base framework widget
    #  and its a ABC wraper. This one should be inherit in the qt widgets and
    #  maybe this should live in the ftrack_ui library? or framework_widget
    #  library. ftrack framework_ui library (this will be the base ABC wrapper)
    #   def connect_widget_signals(self):
    #     if widget:
    #         widget.conetxt_changed.connect_signal(self.context_changed)
    #   def discover_hosts(self):
    #     host_discovered = discover()
    #     if widget:
    #         widget.hosts = host_discovered

    # TODO: change name to available_hosts
    @property
    def host_connections(self):
        '''Return the current list of host_connections'''
        return Client._host_connections

    @host_connections.setter
    def host_connections(self, value):
        '''Return the current list of host_connections'''
        Client._host_connections = value

    # TODO: change this to connected host
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
            self.unsubscribe_host_context_changed()
            Client._host_connection = value
            return
        if self.host_connection and value.host_id == self.host_connection.host_id:
            return

        self.logger.debug('Setting new host connection: {}'.format(value))
        Client._host_connection = value

        # Subscribe log item added
        self.event_manager.subscribe.host_log_item_added(
            self.host_connection.host_id,
            callback=self.on_log_item_added_callback
        )
        # Clean up host_context_change_subscription in case exists
        self.unsubscribe_host_context_changed()
        # Subscribe to host_context_change even though we already subscribed in
        # the host_connection. This is because we want to let the client know
        # that host changed context but also update the host connection to the
        # new context.
        self._host_context_changed_subscribe_id = self.event_manager.subscribe.host_context_changed(
            self.host_connection.host_id, self._host_context_changed_callback
        )
        # Feed change of host and context to client
        self.on_host_changed(self.host_connection)
        self.on_context_changed(self.host_connection.context_id)

    @property
    def host_id(self):
        '''Returns the definitions list of the current host connection'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        return self.host_connection.host_id
    @property
    def context_id(self):
        '''Returns the current context id from host'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        return self.host_connection.context_id

    @context_id.setter
    def context_id(self, context_id):
        '''Sets the context id on current host connection, will throw an exception
        if no host connection is active'''
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
        return self._host_context_changed_subscribe_id

    @property
    def definitions(self):
        '''Returns the definitions list of the current host connection'''
        if not self.host_connection:
            raise Exception('No host connection available')
        return self.host_connection.definitions

    @property
    def definition(self):
        '''Returns the current definition.'''
        return self._definition

    @definition.setter
    def definition(self, value):
        '''Returns the current definition.'''
        # TODO: add a checker to check that the definition is type definition and is in
        #  definitions

        if not self.host_connection:
            self.logger.error(
                "Please set the host connection before setting a definition"
            )
            return
        if value and not self.definitions[value.type].get_first(name=value.name):
            self.logger.error(
                "Invalid definition, choose one from : {}".format(
                    self.definitions
                )
            )
            return

        self._definition = value
        if value:
            # Automatically set the engine of the definition
            self.engine_type = self._definition['_config']['engine_type']
        self.on_definition_changed(self.definition)

    @property
    def engine_type(self):
        '''Return the current engine type'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        '''Return the current engine type'''
        # TODO: add a checker to check that value is a valid engine
        self._engine_type = value

    # TODO: double check how we enable disbale multithreading,
    #  I think we can improve it and make it simpler.
    @property
    def multithreading_enabled(self):
        '''Return True if DCC supports multithreading (write operations)'''
        return self._multithreading_enabled
    # Widget
    @property
    def dialogs(self):
        return self.__dialogs_registry

    @property
    def dialog(self):
        return self._dialog

    @dialog.setter
    def dialog(self, value):
        self.set_active_dialog(self._dialog, value)
        self._dialog = value


    def __init__(
            self,
            event_manager,
            auto_discover_host=True,
            auto_connect_host=True,
            multithreading_enabled=True
    ):
        '''
        Initialise Client with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        # TODO: find a common way of using logs and standarize them
        # Setting logger
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # Create the client id to use to comunicate with UI
        self._id = '{}'.format(uuid.uuid4().hex)

        # Set the event manager
        self._event_manager = event_manager
        # TODO: convert this to a decorator, so whenever something is
        #  multithread it has a decorator and this decorator does the if
        #  multithreadenabled
        # Set multithreading
        self._multithreading_enabled = multithreading_enabled

        # Setting init variables to 0
        self._host_context_changed_subscribe_id = None
        self._definition = None
        self._engine_type = None
        self.__dialogs_registry = {}
        self._dialog = None
        self._auto_connect_host = auto_connect_host

        # TODO: Initializing client
        self.logger.debug('Initialising Client {}'.format(self))

        if auto_discover_host and not self.host_connections:
            self.discover_hosts()

    # Host
    def discover_hosts(self, time_out=3):
        '''
        Find for available hosts during the optional *time_out* and Returns
        a list of discovered :class:`~ftrack_framework_core.client.HostConnection`.

        This removes all previously discovered host connections.
        '''
        # Reset host connections
        self.host_connections = []
        if self.host_connection:
            self.unsubscribe_host_context_changed()
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

        # TODO: update self.host_connections name to available_hosts when doing the task.
        while not self.host_connections:
            delta_time = time.time() - start_time

            if time_out and delta_time >= time_out:
                self.logger.warning('Could not discover any host.')
                break

            self.event_manager.publish.discover_host(callback=self._host_discovered_callback)

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

    # TODO: this should be an ABC
    def on_hosts_discovered(self, host_connections):
        # TODO: add the call to the widget in here.
        '''Callback, hosts has been discovered. Widgets can hook in here.'''
        if self._auto_connect_host:
            # Automatically connect to the first one
            self.host_connection = host_connections[0]
        # Call to widget
        self.event_manager.publish.client_signal_hosts_discovered(self.id)

    # TODO: this should be ABC method
    def on_host_changed(self, host_connection):
        '''Called when the host has been (re-)selected by the user. To be
        overridden by the qt client.'''
        # Call to widget
        self.event_manager.publish.client_signal_host_changed(self.id)
        pass

    # Context
    def _host_context_changed_callback(self, event):
        '''Set the new context ID based on data provided in *event*'''
        # Feed the new context to the client
        self.on_context_changed(event['data']['context_id'])

    # TODO: this should be ABC method
    def on_context_changed(self, context_id):
        '''Called when the context has been set or changed within the host connection, either from this
        client or remote (other client or the host). Should be overridden by client.
        '''
        # Communicate ui that host has changed
        self.event_manager.publish.client_signal_context_changed(self.id)

    def unsubscribe_host_context_changed(self):
        '''Unsubscribe to client context change events'''
        if self.host_context_changed_subscribe_id:
            self.session.event_hub.unsubscribe(
                self.host_context_changed_subscribe_id
            )
            self._host_context_changed_subscribe_id = None

    # Definition
    def on_definition_changed(self, definition):
        self.event_manager.publish.client_signal_definition_changed(self.id)

    def run_definition(self, definition, engine_type):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run the entire given *definition* with the given *engine_type*.

        Callback received at :meth:`_run_definition_callback`
        *definition* Should be type of DefinitionObject
        '''
        self.event_manager.publish.host_run_definition(
            self.host_id,
            definition.to_dict(),
            engine_type,
            self._run_definition_callback
        )

    # TODO: evaluate later once widgets are implemented, this might need to be
    #  converted to ABC method.
    def _run_definition_callback(self, event):
        '''Callback of the :meth:`~ftrack_framework_core.client.run_definition'''
        self.logger.debug("_run_definition_callback event: {}".format(event))

    # Plugin
    def run_plugin(
            self, plugin_definition, plugin_method, engine_type,
            plugin_widget_id=None
    ):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run one single plugin.

        Callback received at :meth:`_run_definition_callback`

        *plugin_data* : Dictionary with the plugin information.

        *method* : method of the plugin to be run
        '''

        self.event_manager.publish.host_run_plugin(
            self.host_id,
            plugin_definition,
            plugin_method,
            engine_type,
            plugin_widget_id,
            self._run_plugin_callback
        )

    # TODO: evaluate later once widgets are implemented, this might need to be
    #  converted to ABC method.
    def _run_plugin_callback(self, event):
        '''Callback of the :meth:`~ftrack_framework_core.client.run_plugin'''
        self.logger.debug("_run_plugin_callback event: {}".format(event))
        self.event_manager.publish.client_notify_ui_run_plugin_result(
            self.id,
            event['data'][0]
        )
        # TODO: send the info back to the UI

    # TODO: This should be an ABC
    def on_log_item_added_callback(self, event):
        '''
        Called when a log item has added in the host.
        Is the old Client notification
        '''
        log_item = event['data']['log_item']
        self.logger.info(
            "Plugin Execution progress: \n "
            "plugin_name: {} \n"
            "plugin_type: {} \n"
            "plugin_status: {} \n"
            "plugin_message: {} \n"
            "plugin_method_result: {} \n"
            "plugin_context_data: {} \n"
            "plugin_data: {} \n"
            "plugin_options: {} \n".format(
                log_item.plugin_name,
                log_item.plugin_type,
                log_item.plugin_status,
                log_item.plugin_message,
                log_item.plugin_method_result,
                log_item.plugin_context_data,
                log_item.plugin_data,
                log_item.plugin_options,
            )
        )
        # TODO: in here we should publish an event to communicate this to the UI
    # UI
    # TODO: how we deal with the definition selector which receives a list of definitions
    # TODO: do the run_widget also
    def run_dialog(self, dialog_class, dialog_options=None):
        # use dialog options to pass options to the dialog like for
        #  example: Dialog= WidgetDialog dialog_options= {definition_plugin: Context_selector}
        #  ---> So this will execute the widget dialog with the widget of the
        #  context_selector in it, it simulates a run_widget).

        # TODO: activate the following check:
        # if not isInstance(FrameworkDialog, dialog_widget):
        #     return 'Not compatibleWidget'
        dialog = dialog_class(
            self.event_manager,
            self.id,
            connect_methods_callback=self._connect_methods_callback,
            connect_setter_property_callback=self._connect_setter_property_callback,
            connect_getter_property_callback=self._connect_getter_property_callback,
            dialog_options=dialog_options
        )
        # Append widget to widgets
        # TODO: maybe better to do it manually without the setter property.
        self._register_dialog(dialog)
        self.dialog = dialog
        self.dialog.show()

    def _register_dialog(self, dialog):
        if dialog.id not in list(self.__dialogs_registry.keys()):
            self.__dialogs_registry[dialog.id] = dialog

    def set_active_dialog(self, old_dialog, new_dialog):
        for dialog in list(self.dialogs.values()):
            dialog.change_focus(old_dialog, new_dialog)

    def _connect_methods_callback(self, method_name, arguments=None, callback=None):
        meth = getattr(self, method_name)
        if not arguments:
            arguments = {}
        result = meth(**arguments)
        if callback:
            callback(result)
        return result

    def _connect_setter_property_callback(self, property_name, value):
        self.__setattr__(property_name, value)

    def _connect_getter_property_callback(self, property_name):
        return self.__getattribute__(property_name)


