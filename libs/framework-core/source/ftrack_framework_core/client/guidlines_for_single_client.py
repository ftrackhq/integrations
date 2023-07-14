# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os
import time
import logging
import copy
import uuid

from six import string_types
import ftrack_api
from ftrack_framework_core import constants
from ftrack_framework_core.log import LogDB
from ftrack_framework_core.log.log_item import LogItem
from ftrack_framework_core.definition import definition_object


# TODO: one single client, multiple engines.
class Client(object):
    '''
    Base client class.
    '''

    ui_types = [constants.UI_TYPE]
    '''Compatible UI for this client.'''
    definition_filters = None
    '''Use only definitions that matches the definition_filters'''
    definition_extensions_filter = None
    '''(Open) Only show definitions and components capable of accept these filename extensions. '''

    _host_connection = None
    '''The singleton host connection used by all clients within the process space / DCC'''
    _host_connections = []
    '''The list of discovered host connections'''

    def __repr__(self):
        return '<Client:{0}>'.format(self.ui_types)

    '''
    Standalone
    client = Client(event_manager)
    publish_definitions = client.get_definitions('publisher')
    client.run_definition(publish_definitions[0], 'publisher_engine') # We don't need the engine type as it is defined inside the definition
    
    # We don't have this now but is a wrapper to the run_definitoin
    client.publish('asset_001', <destination_path>, context) 
    
    WITH UI
    client = Client(event_manager)
    client.selectHost()
    definitions = client_get_definition()
    
    client.run_ui(MayaPublisherWidget)
    client.run_ui(AssemblerWidget, loader_definition)
    maya_widget = client.widgets(MayaPublisherWidget)
    maya_widget.close()
    
    
    # TODO: host selector is a standalone widget and is in the ftrack menu
    
    class Client(object):
        def __init__():
            build
        def run_ui(widget_class): # This is the widgetClass
            self.widgets_registry = {}
            widget = widget_class()
            widget.show()
            self.widgets_registry.extend(id:widget_name, widget:widget)
        def connect_widget_signals():
            for widget in widgets():
                widget.connect(self.func)
        def Notify_client_callback():
            for widget in widgets():
                widget.notify()
        def discover_host():
            client_discover_host()
        def run_definition(definition, engine...):
            run_definition(efinition, engine...)
        def run_plugin(options, callback):
             result = run_plugin('discover_assets', callback)
             callback_fn(result)
        # Method_name should be run_plugin or run_definition)
        def func(method_name, options, callback):
            meth = getAttr(method_name)
            meth(options, callback)
        def get_definition(definition_type):
            return host_connection.definitions['definitions_name']
            
    class FrameworkWidgetBaseABC(ABC):# THis lives inside the framework connect library.        
        client_func = None
        def connect(func):
            self.client_func = func
        @abc
        @property
        def definition():
            return self._definition
        @abc
        def set_definition(definition):
            self._definition = definition
        @abc
        def pre_build():
        @abc
        def build():
        @abc
        def post_build():
        @abc
        def notify(args):
            pass
            
    class PublisherWidget(FrameworkWidgetABC, QFrame):
        
        def __init__(definition):
            build
        def build():
            pass
        def run_button_clicked() # THIS is an ABC method
    
    class MayaPublisherWidget(MayaQWidgetDockableMixin, PublisherWidget):
        def __init__():
        def show(self):
            super(MayaQtPublisherClientWidgetMixin, self).show(
                dockable=True,
                floating=False,
                area='right',
                width=200,
                height=300,
                x=300,
                y=600,
                retain=False,
            )
    
    class AssemblerWidget(FrameworkWidgetABC, QFrame):
        QtCore.Signal(discover_assets, object, object, object)
        def __init__():
            build
        def notify(func):
            self.update_progeres_bar()
        def build():
            resolver_widget = ResolverWidget(am_Definition)
            am_widget = AMWidget(am_definitoin)
            resolver_widget.discover_assets.connect(self.discover_assets)
            resolver_widget.get_definition.connect(self.get_resolver_definition)
        def discover_assets(context):
            self.client_func('discover_assets', options, self.assets_discovered_callback)
            #self.discover_assets.emit(context, <client_method>(discover_assets), self.assets_discovered_callback)
        def get_resolver_definition(definition_type):
            self.client_func('get_definition', definition_type, self.resolver_widget.set_definition)
        def assets_discovered_callback(result):
            fill out the combo box
        
        #def connect_signals():
            
    
    
    '''

    def get_definitions(self, engine_type):
        # This returns definitions available for a specific engine
        pass
    # This should be run_engine
    def run_definition(self, definitiin, engine_type):
        # this reads the definition and runs it in the host
        pass

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


    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`'''
        return self._event_manager

    # TODO: evaluate where do we use this and if its needed, as if host_connection that means that we are connected.
    @property
    def connected(self):
        '''
        Returns True if client is connected to a
        :class:`~ftrack_framework_core.host.HOST`'''
        return self._connected

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
        self.host_connection.on_client_context_changed(context_id)

    # TODO: fix all cantext and context id, try to use always just context ID, if succed, then remove context from everywhere.
    @property
    def context(self):
        '''Returns the current context'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        if self.host_connection.context_id is None:
            raise Exception('No host context id set')
        return self.session.query(
            'Context where id={}'.format(self.context_id)
        ).first()

    # TODO: change name to available_hosts
    @property
    def host_connections(self):
        '''Return the current list of host_connections'''
        return Client._host_connections

    @host_connections.setter
    def host_connections(self, value):
        '''Return the current list of host_connections'''
        Client._host_connections = value

    #TODO: change this to connected host
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
        if value is None or (
            self.host_connection and value.id == self.host_connection.host_id
        ):
            return

        self.logger.debug('host connection: {}'.format(value))
        Client._host_connection = value
        #TODO: try to simplify this and mix this to in a host subscriptions method?
        self.on_client_notification()
        # Clean up host_context_change_subscription in case exists
        self.unsubscribe_host_context_changed()
        # Subscribe to host_context_change even though we already subscribed in
        # the host_connection. This is because we want to notify the widget that
        # context_id has been changed.
        self.host_context_changed_subscribe_id = self.event_manager.events.subscribe.host_context_changed(
            self.host_connection.host_id, self._host_context_changed_callback
        )
        # Feed change of host and context to client
        # TODO: convert the following 2 signals to abstract metods, so always need to be overriden.
        self.on_host_changed(self.host_connection)
        self.on_context_changed(self.host_connection.context_id)

    # TODO: double check if we really need the shcema. I think we don't.
    @property
    def schema(self):
        '''Return the current schema.'''
        return self._schema

    @property
    def definition(self):
        '''Returns the current definition.'''
        return self._definition

    @property
    def definitions(self):
        '''Returns the definitions list of the current host connection'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        return self.host_connection.definitions

    @property
    def engine_type(self):
        '''Return the current engine type'''
        return self._engine_type

    @property
    def logs(self):
        '''Return the log items'''
        self._init_logs()
        return self._logs.get_log_items(
            self.host_connection.host_id
            if not self.host_connection is None
            else None
        )

    def _init_logs(self):
        '''Delayed initialization of logs, when we know host ID.'''
        if self._logs is None:
            self._logs = LogDB(
                self.host_connection.host_id
                if not self.host_connection is None
                else uuid.uuid4().hex
            )

    # TODO: double check how we enable disbale multithreading, I think we can improve it and make it simplest.
    @property
    def multithreading_enabled(self):
        '''Return True if DCC supports multithreading (write operations)'''
        return self._multithreading_enabled

    def __init__(self, event_manager, multithreading_enabled=True):
        '''
        Initialise Client with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        # TODO: we don't use _current, remove it.
        self._current = {}

        #TODO: Can we handle this into the events module?
        self.host_context_changed_subscribe_id = None
        #TODO: is this really necesary? self.host_connection already tell us if we are connected.
        self._connected = False
        self._logs = None
        # TODO: remove this in case we remove schema from the client
        self._schema = None
        self._definition = None

        # TODO: double check, but think that we can remove this as is just use in on_ready method that is only used in tests, so we can remove booth.
        self.__callback = None
        # TODO: find a common way of using logs and standarize them
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._event_manager = event_manager
        # TODO: Initializing client
        self.logger.debug('Initialising {}'.format(self))
        self._multithreading_enabled = multithreading_enabled

    # Host

    def discover_hosts(self, force_rediscover=False, time_out=3):
        '''
        Find for available hosts during the optional *time_out* and Returns
        a list of discovered :class:`~ftrack_framework_core.client.HostConnection`.

        Skip this and use existing singleton host connection if previously detected,
        unless *force_rediscover* is True.
        '''
        # TODO: remove force_rediscover if not used. We will implemented when needed
        if force_rediscover:
            self.host_connections = None
            self.host_connection = None
        #TODO: I think we can remove this from this method. If its used, we should move it to a reconnect method or some similar name.
        if self.host_connection is not None:
            self.on_client_notification()
            # Clean up host_context_change_subscription in case exists
            self.unsubscribe_host_context_changed()
            # Subscribe to host_context_change even though we already subscribed in
            # the host_connection. This is because we want to notify the widget that
            # context_id has been changed.
            self.host_context_changed_subscribe_id = self.event_manager.events.subscribe.host_context_changed(
                self.host_connection.host_id, self._host_context_changed_callback
            )
            self.on_host_changed(self.host_connection)
            self.on_context_changed(self.host_connection.context_id)
            return
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

            self._discover_hosts()

        # TODO: remove this if not needed
        if self.__callback and self.host_connections:
            self.__callback(self.host_connections)

        # TODO: this might need to be called from host discovered? does it makes more sense? because here could be that no host is discovered so no need to call the on_host_discovered method?
        # Feed host connections to the client
        self.on_hosts_discovered(self.host_connections)

    def _discover_hosts(self):
        '''
        Publish an event with the topic
        :py:data:`~ftrack_framework_core.constants.DISCOVER_HOST_TOPIC`
        with the callback
        py:meth:`~ftrack_framework_core.client._host_discovered_callback`
        '''
        # TODO: Move this to events module
        self.host_connections = []  # Start over
        discover_event = ftrack_api.event.base.Event(
            topic=constants.DISCOVER_HOST_TOPIC
        )

        self._event_manager.publish(
            discover_event, callback=self._host_discovered
        )

    def _host_discovered(self, event):
        '''
        Callback, add the :class:`~ftrack_framework_core.client.HostConnection`
        of the new discovered :class:`~ftrack_framework_core.host.HOST` from
        the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        if not event['data']:
            return
        host_connection = HostConnection(self.event_manager, event['data'])
        # TODO: should we remove the filter_host for now as its not used.
        if (
            host_connection
            and host_connection not in self.host_connections
            and self.filter_host(host_connection)
        ):
            #TODO: check if we need to call Client._host_connections or self.host... is enough.
            Client._host_connections.append(host_connection)

        # TODO: this can be removed from here, also doesn't makes sense as here is not yet connected, just discovered.
        self._connected = True

    # TODO: remove this method for now until we need it?
    def filter_host(self, host_connection):
        '''Return True if the *host_connection* should be considered

        *host_connection*: :class:`ftrack_framework_core.client.HostConnection`
        '''
        # On the discovery time context id could be None, so we have to consider
        # hosts with non context id. This method could be useful later on to
        # filter hosts that not match a specific criteria. But considering all
        # hosts as valid for now.
        return True

    # TODO: Shouldn't we use something like set_host? or simply use the setter property?
    def change_host(self, host_connection):
        '''Client(user) has chosen the host connection to use, set it to *host_connection*'''
        self.host_connection = host_connection

   # TODO: should this be ABC method?
    def on_hosts_discovered(self, host_connections):
        '''Callback, hosts has been discovered. To be overridden by the qt client'''
        pass

    # TODO: should this be ABC method?
    def on_host_changed(self, host_connection):
        '''Called when the host has been (re-)selected by the user. To be
        overridden by the qt client.'''
        pass

    # Context

    def _host_context_changed_callback(self, event):
        '''Set the new context ID based on data provided in *event*'''
        # Feed the new context to the client
        self.on_context_changed(event['data']['context_id'])

    # TODO: if used, should this be an ABC method?
    def on_context_changed(self, context_id):
        '''Called when the context has been set or changed within the host connection, either from this
        client or remote (other client or the host). Should be overridden by client.
        '''
        # TODO: we have to add something like  if widget: widget.on_context_changed()
        #  In the widget itself we will import from the wraper widget which is an ABC: from framework_ui_wrappers import widget(this will be what has to be imported in the widget)
        pass

    #TODO: why do we need this one?
    def unsubscribe_host_context_changed(self):
        '''Unsubscribe to client context change events'''
        if self.host_context_changed_subscribe_id:
            self.session.event_hub.unsubscribe(
                self.host_context_changed_subscribe_id
            )
            self.host_context_changed_subscribe_id = None

    # Definition

    # TODO: should this be an ABC method?
    def run_definition(self, definition=None, engine_type=None):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run the entire given *definition* with the given *engine_type*.

        Callback received at :meth:`_run_callback`
        '''
        # TODO: maybe we should always pass the definition and the engine type. And remove the magic of using the set ones, isntead we can call it with self.run_definition(self.definition, self.engine_type)
        # If not definition or engine type passed use the original ones set up
        # in the client
        if not definition:
            definition = self.definition
        if not engine_type:
            engine_type = self.engine_type
        self.host_connection.run_definition(
            definition.to_dict(),
            engine_type,
            # TODO: should we call _run_definition_callback? and run_plugin_callback for the plugin?
            callback=self._run_callback,
        )

    #TODO: I think this is safe to remove as we don't need the schema in the client.
    def get_schema_from_definition(self, definition):
        '''Return matching schema for the given *definition*'''
        if not self.host_connection:
            self.logger.error("please set the host connection first")
            return
        for schema in self.host_connection.definitions['schema']:
            if (
                schema['properties']['type'].get('default')
                == definition['type']
            ):
                return schema

            self.logger.debug(
                "Schema title: {} and type: {} does not match definition {}".format(
                    schema['title'],
                    schema['properties']['type'].get('default'),
                    definition['name'],
                )
            )

        self.logger.error(
            "Can't find a matching schema for the given definition: {}".format(
                definition.name
            )
        )
        return

    # TODO: shouldn't this be something like set_definition or simply call the property setter?
    def change_definition(self, definition, schema=None):
        '''
        Assign the given *schema* and the given *definition* as the current
        :obj:`schema` and :obj:`definition`
        '''
        if not self.host_connection:
            self.logger.error("please set the host connection first")
            return
        if not definition:
            self.logger.error("please provide a definition")
            return

        # TODO: remove the schema part if we remove schema from the client
        if not schema:
            schema = self.get_schema_from_definition(definition)
        self._schema = schema
        self._definition = definition
        self.change_engine(self.definition['_config']['engine_type'])

    # Plugin

    #TODO: should this be an ABC ? maybe not needed.
    def run_plugin(self, plugin_data, method, engine_type):
        '''
        Calls the :meth:`~ftrack_framework_core.client.HostConnection.run`
        to run one single plugin.

        Callback received at :meth:`_run_callback`

        *plugin_data* : Dictionary with the plugin information.

        *method* : method of the plugin to be run
        '''
        # Plugin type is constructed using the engine_type and the type of the plugin.
        # (publisher.collector). We have to make sure that plugin_type is in
        # the data argument passed to the host_connection, because we are only
        # passing data to the engine. And the engine_type is only available
        # on the definition.
        plugin_type = '{}.{}'.format(engine_type, plugin_data['type'])
        data = {
            'plugin': plugin_data,
            'plugin_type': plugin_type,
            'method': method,
        }
        self.host_connection.run_definition(
            data, engine_type, callback=self._run_callback
        )

    # TODO: use diferent callback for plugin and for definition
    def _run_callback(self, event):
        '''Callback of the :meth:`~ftrack_framework_core.client.run_plugin'''
        self.logger.debug("_run_callback event: {}".format(event))

    # TODO: remove this if not used.
    def on_ready(self, callback, time_out=3):
        '''
        calls the given *callback* method when host is been discovered with the
        optional *time_out*
        '''
        self.__callback = callback
        self.discover_hosts(time_out=time_out)

    #TODO: shouldn't this be something like set_engine or simply call the property setter?
    def change_engine(self, engine_type):
        '''
        Assign the given *engine_type* as the current :obj:`engine_type`
        '''
        self._engine_type = engine_type

    #TODO: is this needed? shoudl then this be ABC?
    def _on_log_item_added(self, log_item):
        '''Called when a client notify event arrives.'''
        pass

    def on_client_notification(self):
        '''
        Subscribe to topic
        :const:`~ftrack_framework_core.constants.NOTIFY_CLIENT_TOPIC`
        to receive client notifications from the host in :meth:`_notify_client`
        '''
        # TODO: MOVE this to events module
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.NOTIFY_CLIENT_TOPIC, self.host_connection.host_id
            ),
            self._notify_client,
        )

    # TODO: check if this should be ABC emthod to be overriden in all the client childs or is ok as it is.
    def _notify_client(self, event):
        '''
        Callback of the
        :const:`~ftrack_framework_core.constants.NOTIFY_CLIENT_TOPIC`
         event.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        #TODO: not as priority task, but we might should have a method in events module to parse the events so we don't have to go into data/pipeline all the time.
        result = event['data']['pipeline']['result']
        status = event['data']['pipeline']['status']
        plugin_name = event['data']['pipeline']['plugin_name']
        widget_ref = event['data']['pipeline']['widget_ref']
        message = event['data']['pipeline']['message']
        user_data = event['data']['pipeline'].get('user_data') or {}
        user_message = user_data.get('message')
        plugin_id = event['data']['pipeline'].get('plugin_id')

        # TODO: shouldn't this be add_log_item? and the on_log_item_added is the callback?
        self._on_log_item_added(LogItem(event['data']['pipeline']))

        if constants.status_bool_mapping[status]:
            self.logger.debug(
                '\n plugin_name: {} \n status: {} \n result: {} \n '
                'message: {} \n user_message: {} \n plugin_id: {}'.format(
                    plugin_name,
                    status,
                    result,
                    message,
                    user_message,
                    plugin_id,
                )
            )

        if (
            status == constants.ERROR_STATUS
            or status == constants.EXCEPTION_STATUS
        ):
            raise Exception(
                'An error occurred during the execution of the '
                'plugin name {} \n message: {}  \n user_message: {} '
                '\n data: {} \n plugin_id: {}'.format(
                    plugin_name, message, user_message, result, plugin_id
                )
            )
