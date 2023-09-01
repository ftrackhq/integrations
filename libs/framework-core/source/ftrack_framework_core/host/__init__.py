# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import uuid
import logging
import socket
import os
import time

from functools import partial

from ftrack_utils.framework.dependencies import registry
import ftrack_constants.framework as constants

from ftrack_framework_core.definition import (
    discover,
    validate,
    definition_object,
)
from ftrack_framework_core.host.engine import (
    load_publish,
    asset_manager_to_remove,
    resolver_to_remove,
)
from ftrack_framework_core.asset import FtrackObjectManager
from ftrack_framework_core.log.log_item import LogItem
from ftrack_framework_core.log import LogDB

logger = logging.getLogger(__name__)

# TODO: this is the discover_host_reply function:
#  1. Double check if this should better be part of the host class as a method.
#  2. Rename it to discover_host_reply_callback or similar?


def provide_host_information(
    host_id, host_name, context_id, definitions, event
):
    '''
    Returns dictionary with host id, host name, context id and definition from
    the given *id*, *definitions* and *name*.

    *id* : Host id

    *definitions* : Dictionary with a valid definitions

    *name* : Host name
    '''
    logger.debug('providing id: {}'.format(id))
    host_dict = {
        'host_id': host_id,
        'host_name': host_name,
        'context_id': context_id,
        'definitions': definitions,
    }
    # TODO: we could pass the engines as well so client knows what engines do we
    #  have available. Re-evaluate this as it might not be necessary as the engine
    #  is always given by the definition....
    return host_dict


class Host(object):
    # TODO: double_check host types and host type do we really need it?
    #  Maybe what we need is definitions type? to specify which definitions we
    #  want to discover?
    host_types = [constants.host.PYTHON_HOST_TYPE]
    '''Compatible Host types for this HOST.'''

    # TODO: Engines Dictionary should come from constants.
    #  Should be something CLIENT_NAME:ENGINE:NAME and in here we any have
    #  engines = constant.ENGINES_DICT
    #  Also user should be able to easily create new engine, so maybe we should
    #  be able to discover engines like the plugins and the definitions.
    #   THis should go to a configuration file
    engines = {
        constants.definition.PUBLISHER: load_publish.LoadPublishEngine,
        constants.definition.LOADER: load_publish.LoadPublishEngine,
        constants.definition.OPENER: load_publish.LoadPublishEngine,
        constants.definition.ASSET_MANAGER: asset_manager_to_remove.AssetManagerEngine,
        constants.definition.RESOLVER: resolver_to_remove.ResolverEngine,
    }
    '''Available engines for this host.'''

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
        return self.__schemas_registry

    @property
    def definitions(self):
        '''
        Returns the registered definitions`
        '''
        return self.__definitions_registry

    @property
    def plugins(self):
        '''
        Returns the registered plugins`
        '''
        return self.__plugins_registry

    @property
    def engines(self):
        '''
        Returns the registered engines`
        '''
        return self.__engines_registry

    # TODO: we can create an engine registry

    def __init__(self, event_manager):
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
        self.__definitions_registry = {}
        self.__schemas_registry = []
        self.__plugins_registry = []
        self.__engines_registry = []

        # Register modules
        self._register_modules()
        # Subscribe to events
        self._subscribe_events()

        self.logger.debug('Host {} ready.'.format(self.id))

    # Register
    def _register_modules(self):
        '''
        Register available framework modules.
        '''
        # We register the plugins first so they can subscribe to the discover event
        registry.register_framework_modules_by_type(
            event_manager=self.event_manager,
            module_type='plugins',
            callback=self._on_register_plugins_callback,
        )
        # Register the schemas before the definitions
        registry.register_framework_modules_by_type(
            event_manager=self.event_manager,
            module_type='schemas',
            callback=self._on_register_schemas_callback,
        )
        # Make sure schemas are found
        if not self.schemas:
            raise Exception(
                'No schemas found. Please register valid schemas first.'
            )
        # Register the definitions, passing the schemas in the callback as are
        # needed to augment and validate the definitions.
        registry.register_framework_modules_by_type(
            event_manager=self.event_manager,
            module_type='definitions',
            callback=partial(
                self._on_register_definitions_callback, self.schemas
            ),
        )

        # Register engines
        registry.register_framework_modules_by_type(
            event_manager=self.event_manager,
            module_type='engines',
            callback=self._on_register_engines_callback
        )

        if (
            self.__plugins_registry
            and self.__schemas_registry
            and self.__definitions_registry
            and self.__engines_registry
        ):
            # Check that registry went correct
            return True
        raise Exception('Error registering modules on host, please check logs')

    def _on_register_plugins_callback(self, registered_plugins):
        '''
        Callback of the :meth:`_register_framework_modules` of type plugins.
        We add all the *registered_plugins* into our
        :obj:`self.__plugins_registry`
        '''
        registered_plugins = list(set(registered_plugins))
        initialized_plugins = []
        # Init plugins
        for plugin in registered_plugins:
            initialized_plugins.append(
                plugin(self.event_manager, self.id, self.ftrack_object_manager)
            )

        self.__plugins_registry = initialized_plugins

    def _on_register_schemas_callback(self, schema_paths):
        '''
        Callback of the :meth:`_register_framework_modules` of type schmas.
        We will discover valid schemas from all given *schema_paths* and convert
        them to schemaObject. Valid schemas will be added to
        :obj:`self.__schemas_registry`
        '''
        schema_paths = list(set(schema_paths))

        schemas = self._discover_schemas(schema_paths)

        self.__schemas_registry = schemas

    def _on_register_definitions_callback(self, schemas, definition_paths):
        '''
        Callback of the :meth:`_register_framework_modules` of type definitions.
        We will discover valid definitions from all given *definition_paths*
        based on the given *schemas* and will convert the valid ones to a
        DefinitionObject. Valid definitions will be added to
        :obj:`self.__definition_registry`
        '''
        definition_paths = list(set(definition_paths))

        definitions = self._discover_definitions(
            definition_paths, self.host_types, schemas
        )

        self.__definitions_registry = definitions

    def _on_register_engines_callback(self, registred_engines):
        registred_engines = list(set(registred_engines))
        initialized_enignes = []
        # Init engines
        for engine in registred_engines:
            initialized_enignes.append(
                engine(self.event_manager, self.id, self.ftrack_object_manager)
            )

        self.__engines_registry = initialized_enignes

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

    def _discover_definitions(self, definition_paths, host_types, schemas):
        '''
        Discover all the available and valid definitions in the given
        *definition_paths* compatible with the given *host_types* and given
        *schemas*
        '''
        start = time.time()

        # discover definitions
        discovered_definitions = discover.discover_definitions(
            definition_paths
        )

        # filter definitions
        discovered_definitions = discover.filter_definitions_by_host(
            discovered_definitions, host_types
        )

        # validate schemas
        discovered_definitions = discover.augment_definition(
            discovered_definitions, schemas, self.session
        )

        # validate_plugins
        validated_definitions = discover.discover_definitions_plugins(
            discovered_definitions, self.event_manager, self.host_types
        )

        end = time.time()
        logger.debug('Discover definitions run in: {}s'.format((end - start)))

        for key, value in list(validated_definitions.items()):
            logger.warning(
                'Valid definitions : {} : {}'.format(key, len(value))
            )

        return validated_definitions

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
            self.definitions,
        )
        self.event_manager.subscribe.discover_host(
            callback=discover_host_callback_reply
        )
        # Subscribe to run definition
        self.event_manager.subscribe.host_run_definition(
            self.id, self.run_definition_callback
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
    def run_definition_callback(self, event):
        '''
        Runs the data with the defined engine type of the given *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        definition = event['data']['definition']
        engine_type = event['data']['engine_type']
        # TODO: Double check the asset_type_name workflow, it isn't clean.
        asset_type_name = definition.get('asset_type')

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
            validate.validate_definition(self.schemas, definition)
        except Exception as error:
            self.logger.error(
                "Can't validate definition {} error: {}".format(
                    definition, error
                )
            )
        engine_result = engine.run_definition(definition)

        if not engine_result:
            self.logger.error("Couldn't run definition {}".format(definition))
        return engine_result

    # TODO: this should be ABC
    def run_plugin_callback(self, event):
        '''
        Runs the plugin_definition in the given *event* with the engine type
        set in the *event*
        '''

        plugin_definition = event['data']['plugin_definition']
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
            plugin_name=plugin_definition.get('plugin'),
            plugin_default_method=plugin_definition.get('default_method'),
            # plugin_data will usually be None, but can be defined in the
            # definition
            # I have registered data in the publisher schema
            plugin_data=plugin_definition.get('data'),
            plugin_options=plugin_definition.get('options'),
            # plugin_context_data will usually be None, but can be defined in the
            # definition
            # I have registered context_data in the schema
            plugin_context_data=plugin_definition.get('context_data'),
            plugin_method=plugin_method,
            plugin_widget_id=plugin_widget_id,
            plugin_widget_name=plugin_definition.get('widget'),
        )

        if not engine_result:
            self.logger.error(
                "Couldn't run plugin:\n "
                "Definition: {}\n"
                "Method: {}\n"
                "Engine type: {}\n"
                "Engine name: {}\n".format(
                    plugin_definition, plugin_method, engine_type, engine_name
                )
            )
        return engine_result
