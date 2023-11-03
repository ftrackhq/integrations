# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import uuid
import logging
import socket
import os
import time

from functools import partial

import ftrack_constants.framework as constants

from ftrack_framework_core.tool_config import (
    discover,
    validate,
    tool_config_object,
)
from ftrack_framework_core.asset import FtrackObjectManager
from ftrack_framework_core.log.log_item import LogItem
from ftrack_framework_core.log import LogDB

logger = logging.getLogger(__name__)

# TODO: this is the discover_host_reply function:
#  1. Double check if this should better be part of the host class as a method.
#  2. Rename it to discover_host_reply_callback or similar?


def provide_host_information(
    host_id, host_name, context_id, tool_configs, event
):
    '''
    Returns dictionary with host id, host name, context id and tool_config from
    the given *id*, *tool_configs* and *name*.

    *id* : Host id

    *tool_configs* : Dictionary with a valid tool_configs

    *name* : Host name
    '''
    logger.debug('providing id: {}'.format(id))
    host_dict = {
        'host_id': host_id,
        'host_name': host_name,
        'context_id': context_id,
        'tool_configs': tool_configs,
    }
    # TODO: we could pass the engines as well so client knows what engines do we
    #  have available. Re-evaluate this as it might not be necessary as the engine
    #  is always given by the tool_config....
    return host_dict


class Host(object):
    # TODO: double_check host types and host type do we really need it?
    #  Maybe what we need is tool_configs type? to specify which tool_configs we
    #  want to discover?
    host_types = [constants.host.PYTHON_HOST_TYPE]
    '''Compatible Host types for this HOST.'''

    FtrackObjectManager = FtrackObjectManager
    '''FtrackObjectManager class to use'''

    def __repr__(self):
        return '<Host:{0}>'.format(self.id)

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

    @property
    def ftrack_object_manager(self):
        '''
        Initializes and returns an instance of
        :class:`~ftrack_framework_core.asset.FtrackObjectManager`
        '''
        if not isinstance(
            self._ftrack_object_manager, self.FtrackObjectManager
        ):
            self._ftrack_object_manager = self.FtrackObjectManager(
                self.event_manager
            )
        return self._ftrack_object_manager

    @property
    def context_id(self):
        '''Return the default context id set at host launch'''
        # We get the host id from the env variable in case we start from C2
        # TODO: connect3 pass context id when init host, so no need to store it
        #  in an env variable
        return os.getenv(
            'FTRACK_CONTEXTID',
            os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID')),
        )

    @context_id.setter
    def context_id(self, value):
        '''
        Set the context id to *value* and send event to clients
        (through host connections)
        '''
        if value == self.context_id:
            return
        # Storing a context in the environment variable to be picked by connect
        os.environ['FTRACK_CONTEXTID'] = value
        self.logger.warning(
            'ftrack host context is now: {}'.format(self.context_id)
        )
        # Need to unsubscribe to make sure we subscribe again with the new
        # context
        self.session.event_hub.unsubscribe(self._discover_host_subscribe_id)
        # Reply to discover_host_callback to clients to pass the host information
        discover_host_callback_reply = partial(
            provide_host_information,
            self.id,
            self.name,
            self.context_id,
            self.tool_configs,
        )
        self._discover_host_subscribe_id = (
            self.event_manager.subscribe.discover_host(
                callback=discover_host_callback_reply
            )
        )
        self.event_manager.publish.host_context_changed(
            self.id, self.context_id
        )

    @property
    def id(self):
        '''Returns the current host id.'''
        return self._id

    @property
    def name(self):
        '''Returns the current host name'''
        if not self.id:
            return
        host_types = self.id.split("-")[0]
        name = '{}-{}'.format(host_types, socket.gethostname())
        return name

    @property
    def logs(self):
        '''Returns the current logs'''
        if not self._logs:
            self._logs = LogDB(self._id)
        return self._logs

    @property
    def schemas(self):
        '''
        Returns the registered schemas`
        '''
        return self.__schemas_discovered

    @property
    def tool_configs(self):
        '''
        Returns the registered tool_configs`
        '''
        return self.__tool_configs_discovered

    @property
    def plugins(self):
        '''
        Returns the registered plugins`
        '''
        return self.__plugins_discovered

    @property
    def engines(self):
        '''
        Returns the registered engines`
        '''
        return self.__engines_discovered

    # TODO: we can create an engine registry

    def __init__(self, event_manager, registry):
        '''
        Initialise Host with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        # Create the host id
        self._id = '{}-{}'.format('.'.join(self.host_types), uuid.uuid4().hex)

        self.logger.debug('Initializing Host {}'.format(self))

        # Reset Logs
        self._logs = None
        # Set event manager and object manager
        self._event_manager = event_manager
        self._ftrack_object_manager = None
        # Reset all registries
        self.__tool_configs_discovered = {}
        self.__schemas_discovered = {}
        self.__plugins_discovered = []
        self.__engines_discovered = {}
        self._discover_host_subscribe_id = None

        # Register modules
        self._register_modules(registry)
        # Subscribe to events
        self._subscribe_events()

        self.logger.debug('Host {} ready.'.format(self.id))

    # Register
    def _register_modules(self, registry):
        '''
        Register available framework modules.
        '''
        # Discover plugin modules
        self.discover_plugins(registry.plugins)
        # Discover schema modules
        self.discover_schemas(registry.schemas)
        if not self.schemas:
            raise Exception(
                'No schemas found. Please register valid schemas first.'
            )
        # Discover tool-config modules
        self.discover_tool_configs(registry.tool_configs, self.schemas)
        # Discover engine modules
        self.discover_engines(registry.engines)

        if (
            self.__plugins_discovered
            and self.__schemas_discovered
            and self.__tool_configs_discovered
            and self.__engines_discovered
        ):
            # Check that registry went correct
            return True
        raise Exception('Error registering modules on host, please check logs')

    def discover_plugins(self, registered_plugins):
        '''
        Initialize all plugins given in the *registered_plugins* and add the
        initialized plugins into our
        :obj:`self.__plugins_discovered`
        '''

        initialized_plugins = []
        # Init plugins
        for plugin in registered_plugins:
            initialized_plugins.append(
                # TODO: this will be changed on the yaml task and will not have
                #  to be initialized
                plugin['cls'](
                    self.event_manager, self.id, self.ftrack_object_manager
                )
            )

        self.__plugins_discovered = initialized_plugins

    def discover_schemas(self, registered_schemas):
        '''
        We will discover valid schemas from all given *schema_paths* and convert
        them to schemaObject. Valid schemas will be added to
        :obj:`self.__schemas_discovered`
        '''

        # TODO: this should be changed once yml implemented.
        schemas = self._discover_schemas(
            [schema['cls'] for schema in registered_schemas]
        )

        self.__schemas_discovered = schemas

    def discover_tool_configs(self, registered_tool_configs, schemas):
        '''
        We will discover valid tool_configs from all given
        *registered_tool_configs* based on the given *schemas* and will convert
        the valid ones to aToolConfigObject. Valid tool_configs will be added to
        :obj:`self.__tool_config_registry`
        '''
        # TODO: this should be changed once yml implemented.
        tool_configs = self._discover_tool_configs(
            [tool_config['cls'] for tool_config in registered_tool_configs],
            self.host_types,
            schemas,
        )

        self.__tool_configs_discovered = tool_configs

    def discover_engines(self, registered_engines):
        ''' '
        Initialize all engines given in the *registered_engines* and add the
        initialized engines into our
        :obj:`self.__engines_discovered`
        '''
        # Init engines
        for engine in registered_engines:
            # TODO: this will be changed on the yaml task and will not have to
            #  be initialized
            initialized_enigne = engine['cls'](
                self.event_manager,
                self.ftrack_object_manager,
                self.host_types,
                self.id,
            )
            for engine_type in initialized_enigne.engine_types:
                if engine_type not in list(self.__engines_discovered.keys()):
                    self.__engines_discovered[engine_type] = {}
                self.__engines_discovered[engine_type].update(
                    {initialized_enigne.name: initialized_enigne}
                )

        for key, value in list(self.__engines_discovered.items()):
            self.logger.warning(
                'Valid engines : {} : {}'.format(key, len(value))
            )

    # Discover
    def _discover_schemas(self, schema_paths):
        '''
        Discover all available and calid schemas in the given *schema_paths*
        '''
        start = time.time()

        # discover schemas
        discovered_schemas = discover.discover_schemas(schema_paths)

        # resolve schemas
        valid_schemas = discover.resolve_schemas(discovered_schemas)

        end = time.time()
        logger.debug('Discover schemas run in: {}s'.format((end - start)))

        return valid_schemas

    def _discover_tool_configs(self, tool_config_paths, host_types, schemas):
        '''
        Discover all the available and valid tool_configs in the given
        *tool_config_paths* compatible with the given *host_types* and given
        *schemas*
        '''
        start = time.time()

        # discover tool_configs
        discovered_tool_configs = discover.discover_tool_configs(
            tool_config_paths
        )

        # filter tool_configs
        discovered_tool_configs = discover.filter_tool_configs_by_host(
            discovered_tool_configs, host_types
        )

        # validate schemas
        discovered_tool_configs = discover.augment_tool_config(
            discovered_tool_configs, schemas
        )

        # validate_plugins
        registred_plugin_names = [plugin.name for plugin in self.plugins]
        validated_tool_configs = validate.validate_tool_config_plugins(
            discovered_tool_configs, registred_plugin_names
        )

        end = time.time()
        logger.debug('Discover tool_configs run in: {}s'.format((end - start)))

        for key, value in list(validated_tool_configs.items()):
            logger.warning(
                'Valid tool_configs : {} : {}'.format(key, len(value))
            )

        return validated_tool_configs

    # Subscribe
    def _subscribe_events(self):
        '''Host subscription events to communicate with the client'''
        # Subscribe to topic
        # :const:`~ftrack_framework_core.constants.NOTIFY_PLUGIN_PROGRESS_TOPIC`
        # to receive client notifications from the host in :meth:`_notify_client_callback`
        self.event_manager.subscribe.notify_plugin_progress_client(
            self.id, self._notify_plugin_progress_client_callback
        )

        # Listen to context change events for this host and its connected clients
        self.event_manager.subscribe.client_context_changed(
            self.id, self._client_context_change_callback
        )

        # Reply to discover_host_callback to clints to pass the host information
        discover_host_callback_reply = partial(
            provide_host_information,
            self.id,
            self.name,
            self.context_id,
            self.tool_configs,
        )
        self._discover_host_subscribe_id = (
            self.event_manager.subscribe.discover_host(
                callback=discover_host_callback_reply
            )
        )
        # Subscribe to run tool_config
        self.event_manager.subscribe.host_run_tool_config(
            self.id, self.run_tool_config_callback
        )
        # Subscribe to run plugin
        self.event_manager.subscribe.host_run_plugin(
            self.id, self.run_plugin_callback
        )

    def _notify_plugin_progress_client_callback(self, event):
        '''
        Callback of the
        :const:`~ftrack_framework_core.constants.NOTIFY_PLUGIN_PROGRESS_TOPIC`
         event. Stores a log item in host pipeline log DB.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        # Get the plugin info dictionary and add it to the logDB
        plugin_info = event['data']
        log_item = LogItem(plugin_info)
        self.logs.add_log_item(log_item)
        # Publish the event to notify client
        self.event_manager.publish.host_log_item_added(self.id, log_item)

    def _client_context_change_callback(self, event):
        '''Callback when the client has changed context'''
        context_id = event['data']['context_id']
        if context_id != self.context_id:
            self.context_id = context_id

    # Run
    # TODO: this should be ABC
    def run_tool_config_callback(self, event):
        '''
        Runs the data with the defined engine type of the given *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        tool_config = event['data']['tool_config']
        engine_type = tool_config['engine_type']
        engine_name = tool_config['engine_name']
        # TODO: Double check the asset_type_name workflow, it isn't clean.
        # TODO: pick asset type from context plugin and not from tool_config
        asset_type_name = "script"  # tool_config.get('asset_type')

        engine = None
        try:
            engine = self.engines[engine_type].get(engine_name)
        except Exception:
            raise Exception(
                'No engine of type "{}" with name "{}" found'.format(
                    engine_type, engine_name
                )
            )
        # TODO: review asset_type_name in the specific task
        engine.asset_type_name = asset_type_name

        try:
            validate.validate_tool_config(self.schemas, tool_config)
        except Exception as error:
            raise Exception(
                "Can't validate tool_config {} error: {}".format(
                    tool_config, error
                )
            )
        engine_result = engine.run_tool_config(
            tool_config_object.ToolConfigObject(tool_config)
        )

        if not engine_result:
            self.logger.error(
                "Couldn't run tool_config {}".format(tool_config)
            )
        return engine_result

    # TODO: this should be ABC
    def run_plugin_callback(self, event):
        '''
        Runs the plugin_config in the given *event* with the engine type
        set in the *event*
        '''

        plugin_config = event['data']['plugin_config']
        plugin_method = event['data']['plugin_method']
        engine_type = event['data']['engine_type']
        engine_name = event['data']['engine_name']
        plugin_widget_id = event['data']['plugin_widget_id']

        engine = None
        try:
            engine = self.engines[engine_type].get(engine_name)
        except Exception:
            raise Exception(
                'No engine of type "{}" with name "{}" found'.format(
                    engine_type, engine_name
                )
            )
        # TODO: review asset_type_name in the specific task
        engine.asset_type_name = None

        engine_result = engine.run_plugin(
            plugin_name=plugin_config.get('plugin_name'),
            plugin_default_method=plugin_config.get('default_method'),
            # plugin_data will usually be None, but can be defined in the
            # tool_config
            # I have registered data in the publisher schema
            plugin_data=plugin_config.get('data'),
            plugin_options=plugin_config.get('options'),
            # plugin_context_data will usually be None, but can be defined in the
            # tool_config
            # I have registered context_data in the schema
            plugin_context_data=plugin_config.get('context_data'),
            plugin_method=plugin_method,
            plugin_widget_id=plugin_widget_id,
            plugin_widget_name=plugin_config.get('widget_name'),
        )

        if not engine_result:
            self.logger.error(
                "Couldn't run plugin:\n "
                "Tool config: {}\n"
                "Method: {}\n"
                "Engine type: {}\n"
                "Engine name: {}\n".format(
                    plugin_config, plugin_method, engine_type, engine_name
                )
            )
        return engine_result
