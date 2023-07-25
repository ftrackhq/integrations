# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import uuid
import pkgutil
import ftrack_api
import logging
import socket
import os
import time

from ftrack_framework_core.definition import discover, validate
from ftrack_framework_core.host.engine import load_publish, asset_manager, resolver
from ftrack_framework_core.asset import FtrackObjectManager
from ftrack_framework_core import constants, utils

from functools import partial
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
    the given *host_id*, *definitions* and *host_name*.

    *host_id* : Host id

    *definitions* : Dictionary with a valid definitions

    *host_name* : Host name
    '''
    logger.debug('providing host_id: {}'.format(host_id))
    host_dict = {
        'host_id': host_id,
        'host_name': host_name,
        'context_id': context_id,
        'definition': definitions,
    }
    return host_dict

# TODO: we maight need to init the FtrackObjectManager in the host and pass it
#  to the engine and engine to the plugins. Because host is overriden in all the
#  DCC and engines might not
class Host(object):
    # TODO: double_check host types and host type
    host_types = [constants.HOST_TYPE]
    '''Compatible Host types for this HOST.'''

    # TODO: Engines Dictionary should come from constants.
    #  Should be something CLIENT_NAME:ENGINE:NAME and in here we any have
    #  engines = constant.ENGINES_DICT
    #  Also user should be able to easily create new engine, so maybe we should
    #  be able to discover engines like the plugins and the definitions.
    #   THis should go to a configuration file
    engines = {
        constants.PUBLISHER: load_publish.LoadPublishEngine,
        constants.LOADER: load_publish.LoadPublishEngine,
        constants.OPENER: load_publish.LoadPublishEngine,
        constants.ASSET_MANAGER: asset_manager.AssetManagerEngine,
        constants.RESOLVER: resolver.ResolverEngine,
    }
    '''Available engines for this host.'''

    FtrackObjectManager = FtrackObjectManager
    '''FtrackObjectManager class to use'''

    def __repr__(self):
        return '<Host:{0}>'.format(self.host_id)

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`'''
        return self._event_manager

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
        '''Return the the default context id set at host launch'''
        # We get the host id from the env variable in case we start from C2
        # TODO: connect3 pass context id when init host, so no need to store it
        #  in an env variable
        return os.getenv(
            'FTRACK_CONTEXTID',
            os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID')),
        )

    @context_id.setter
    def context_id(self, value):
        '''Set the context id to *value* and send event to clients (through host connections)'''
        if value == self.context_id:
            return
        # TODO: RE-evaluate if we need to store the context to an environment variable
        os.environ['FTRACK_CONTEXTID'] = value
        self.logger.warning(
            'ftrack host context is now: {}'.format(self.context_id)
        )
        self.event_manager.publish.host_context_changed(
            self.host_id,
            self.context_id
        )

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._host_id

    @property
    def host_name(self):
        '''Returns the current host name'''
        if not self.host_id:
            return
        host_types = self.host_id.split("-")[0]
        host_name = '{}-{}'.format(host_types, socket.gethostname())
        return host_name

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    @property
    def schemas(self):
        '''
        Returns the registred schemas`
        '''
        return self.__schemas_registry

    @property
    def definitions(self):
        '''
        Returns the registred definitions`
        '''
        return self.__definitions_registry

    @property
    def plugins(self):
        '''
        Returns the registred definitions`
        '''
        return self.__plugins_registry

    def __init__(self, event_manager):
        '''
        Initialise Host with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._host_id = '{}-{}'.format(
            '.'.join(self.host_types), uuid.uuid4().hex
        )
        self._logs = None

        #TODO: initializing host
        self.logger.debug('initializing {}'.format(self))
        self._event_manager = event_manager
        self._ftrack_object_manager = None
        self.__definitions_registry = {}
        self.__schemas_registry = []
        self.__plugins_registry = []
        # TODO: split the register method to publish_events, subcribe_events or
        #  find some standard way to do it around all the framework modules. Maybe register its ok, but make sure its
        #  not confusing with the register function of the definitions.
        self.register()

    def run_definition(self, event):
        '''
        Runs the data with the defined engine type of the given *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        definition = event['data']['definition']
        engine_type = event['data']['engine_type']
        asset_type_name = definition.get('asset_type')

        Engine = self.engines.get(engine_type)
        if Engine is None:
            # TODO: should we have our own exceptions? So they automatically registers to log as well.
            raise Exception('No engine of type "{}" found'.format(engine_type))
        engine_runner = Engine(
            self.event_manager, self.ftrack_object_manager, self.host_types,
            self.host_id, asset_type_name
        )

        try:
            validate.validate_definition(self.schemas, definition)
        except Exception as error:
            self.logger.error(
                "Can't validate definition {} error: {}".format(definition, error)
            )
        runner_result = engine_runner.run_definition(definition)

        if runner_result == False:
            self.logger.error("Couldn't run efinition {}".format(definition))
        return runner_result

    def run_plugin(self, event):
        '''
        Runs the data with the defined engine type of the givent *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        plugin_definition = event['data']['plugin_definition']
        plugin_method = event['data']['plugin_method']
        engine_type = event['data']['engine_type']

        Engine = self.engines.get(engine_type)
        if Engine is None:
            # TODO: should we have our own exceptions? So they automatically registers to log as well.
            raise Exception('No engine of type "{}" found'.format(engine_type))
        engine_runner = Engine(
            self.event_manager, self.ftrack_object_manager, self.host_types,
            self.host_id, None
        )

        runner_result = engine_runner.run_plugin(
            plugin_definition=plugin_definition,
            # plugin_data will usually be None, but can be defined in the
            # definition
            plugin_data=plugin_definition.get('plugin_data'),
            plugin_options=plugin_definition.get('options'),
            # plugin_context_data will usually be None, but can be defined in the
            # definition
            plugin_context_data=plugin_definition.get('context_data'),
            plugin_method=plugin_method
        )

        if runner_result == False:
            self.logger.error(
                "Couldn't run plugin:\n "
                "Definition: {}\n"
                "Method: {}\n"
                "Engine: {}\n".format(plugin_definition, plugin_method, engine_type)
            )
        return runner_result

    # TODO: remove this if we do a direct registry
    # def _on_register_definition_callback(self, event):
    #     '''
    #     Callback of the :meth:`register`
    #     Validates the given *event* and subscribes to the
    #     :class:`ftrack_api.event.base.Event` events with the topics
    #     :const:`~ftrack_connnect_pipeline.constants.DISCOVER_HOST_TOPIC`
    #     and :const:`~ftrack_connnect_pipeline.constants.HOST_RUN_DEFINITION_TOPIC`
    #
    #     *event* : Should be a validated and complete definitions, schema and
    #     packages dictionary coming from
    #     :func:`ftrack_connect_pipeline_definition.resource.definitions.register._register_definitions_callback`
    #     '''
    #
    #     raw_result = event['data']
    #
    #     if not raw_result:
    #         return
    #
    #     # Raw data should contain host_types and definition_paths
    #     host_types = list(set(raw_result.get("host_types")))
    #     definition_paths = list(set(raw_result.get("definition_paths")))
    #
    #     definitions, schemas = self.collect_and_validate_definitions(
    #         definition_paths, host_types
    #     )
    #
    #     # TODO: rename this to __schema_registry or __definitions_registry. Also make sure its initialized in the init.
    #     self.__definitions_registry = definitions
    #     self.__definitions_registry['schemas'] = schemas
    #
    #     discover_host_callback_reply = partial(
    #         provide_host_information,
    #         self.host_id,
    #         self.host_name,
    #         self.context_id,
    #         definitions,
    #     )
    #
    #     self.event_manager.subscribe.discover_host(
    #         callback=discover_host_callback_reply
    #     )
    #
    #     # TODO: change the run callback to run_definiton
    #     self.event_manager.events.subscribe.host_run_definition(self.host_id, self.run_definition)
    #     # TODO: create the run_plugin method (pick the desired parts from the current self.run plugin)
    #     #  Carefully, run plugin topic was already used by engines to be able to run plugins, so the run plugin function wasn't existing int the host. We will have to separate this 2 events maybe.
    #     self.event_manager.events.subscribe.host_run_plugin(self.host_id, self.run_plugin)
    #     self.logger.debug('host {} ready.'.format(self.host_id))

    def _init_logs(self):
        '''Delayed initialization of logs, when we know host ID.'''
        if self._logs is None:
            self._logs = LogDB(self._host_id)

    def _on_client_notification(self, event):
        '''
        Callback of the
        :const:`~ftrack_framework_core.constants.NOTIFY_CLIENT_TOPIC`
         event. Stores a log item in host pipeline log DB.

        *event*: :class:`ftrack_api.event.base.Event`
        '''

        self._init_logs()
        # TODO: all data/pipeline events should come from data/framework or data/  events.
        self._logs.add_log_item(LogItem(event['data']['pipeline']))

    def register(self):
        '''
        Publishes the :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.DISCOVER_DEFINITION_TOPIC`
        with the first host_type in the list :obj:`host_types` and type definition as the
        data.

        Callback of the event points to :meth:`_on_register_definition_callback`
        '''

        # Publish event to discover definition. For now its not available as its
        # not worth if all are local dependencies.
        # self.event_manager.publish.discover_definition(
        #     host_types=self.host_types, callback=self._on_register_definition_callback
        # )
        # TODO: remove temp if we go for this design
        # We register the plugins first so they can subscribe to the discover event
        self._register_framework_modules(
            type='plugins', callback=self._on_register_plugins_callback_temp
        )
        # Register the schemas befor the definitions
        self._register_framework_modules(
            type='schemas', callback=self._on_register_schemas_callback_temp
        )
        # Make sure schemas are found
        if not self.schemas:
            raise Exception(
                'No schemas found. Please register valid schemas first.'
            )
        # Register the definitions, passing the shcemas in the callback as are
        # needed to augment and validate the definitions.
        self._register_framework_modules(
            type='definitions', callback=partial(
                self._on_register_definitions_callback_temp, self.schemas
            )
        )

        '''
        Subscribe to topic
        :const:`~ftrack_framework_core.constants.NOTIFY_CLIENT_TOPIC`
        to receive client notifications from the host in :meth:`_notify_client_callback`
        '''
        self.event_manager.subscribe.notify_client(
            self.host_id, self._on_client_notification
        )

        ''' Listen to context change events for this host and its connected clients'''
        self.event_manager.subscribe.client_context_changed(
            self.host_id, self._change_context_id
        )

    def _register_framework_modules(self, type, callback):
        registry_result = []
        for package in pkgutil.iter_modules():
            is_type = all(x in package.name.split("_") for x in ['ftrack', 'framework', type])
            if not is_type:
                continue
            register_module = getattr(__import__(package.name, fromlist=['register']), 'register')
            # Register by event
            # register_module.register(self.session)
            # register by direct connection
            # TODO: we need to pass event manager, host id
            result = register_module.register()
            if type(result) == list:
                registry_result.extend(register_module.register())
                continue
            registry_result.append(register_module.register())

        if registry_result:
            callback(registry_result)

    def _on_register_definitions_callback_temp(self, schemas, definition_paths):
        '''
        Callback of the :meth:`register`
        Validates the given *event* and subscribes to the
        :class:`ftrack_api.event.base.Event` events with the topics
        :const:`~ftrack_connnect_pipeline.constants.DISCOVER_HOST_TOPIC`
        and :const:`~ftrack_connnect_pipeline.constants.HOST_RUN_DEFINITION_TOPIC`

        *event* : Should be a validated and complete definitions, schema and
        packages dictionary coming from
        :func:`ftrack_connect_pipeline_definition.resource.definitions.register._register_definitions_callback`
        '''
        definition_paths = list(set(definition_paths))

        definitions, schemas = self._discover_definitions(
            definition_paths, self.host_types, schemas
        )

        #TODO: can we convert definitions to FtrackDefinitionObject in here and
        # pass it through the event? or better to revceive it as json in client
        # and convert it in there?

        self.__definitions_registry = definitions

        discover_host_callback_reply = partial(
            provide_host_information,
            self.host_id,
            self.host_name,
            self.context_id,
            self.definitions,
        )

        self.event_manager.subscribe.discover_host(
            callback=discover_host_callback_reply
        )

        # TODO: change the run callback to run_definiton
        self.event_manager.events.subscribe.host_run_definition(self.host_id, self.run_definition)
        # TODO: create the run_plugin method (pick the desired parts from the current self.run plugin)
        #  Carefully, run plugin topic was already used by engines to be able to run plugins, so the run plugin function wasn't existing int the host. We will have to separate this 2 events maybe.
        self.event_manager.events.subscribe.host_run_plugin(self.host_id, self.run_plugin)
        self.logger.debug('host {} ready.'.format(self.host_id))

    def _on_register_schemas_callback_temp(self, schema_paths):
        '''
        Callback of the :meth:`register`
        Validates the given *event* and subscribes to the
        :class:`ftrack_api.event.base.Event` events with the topics
        :const:`~ftrack_connnect_pipeline.constants.DISCOVER_HOST_TOPIC`
        and :const:`~ftrack_connnect_pipeline.constants.HOST_RUN_DEFINITION_TOPIC`

        *event* : Should be a validated and complete definitions, schema and
        packages dictionary coming from
        :func:`ftrack_connect_pipeline_definition.resource.definitions.register._register_definitions_callback`
        '''
        schema_paths = list(set(schema_paths))

        schemas = self._discover_schemas(schema_paths, self.host_types)

        self.__schemas_registry = schemas

    def _on_register_plugins_callback_temp(self, registred_plugins):
        '''
        Callback of the :meth:`register`
        Validates the given *event* and subscribes to the
        :class:`ftrack_api.event.base.Event` events with the topics
        :const:`~ftrack_connnect_pipeline.constants.DISCOVER_HOST_TOPIC`
        and :const:`~ftrack_connnect_pipeline.constants.HOST_RUN_DEFINITION_TOPIC`

        *event* : Should be a validated and complete definitions, schema and
        packages dictionary coming from
        :func:`ftrack_connect_pipeline_definition.resource.definitions.register._register_definitions_callback`
        '''
        registred_plugins = list(set(registred_plugins))

        self.__plugins_registry = registred_plugins


    def _discover_definitions(self, definition_paths, host_types, schemas):
        '''
        Collects all json files from the given *definition_paths* that match
        the given *host_types*
        '''
        start = time.time()

        # discover definitions
        discovered_definitions = discover.discover_definitions(definition_paths)

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

    def _discover_schemas(self, schema_paths, host_types):
        '''
        Collects all json files from the given *definition_paths* that match
        the given *host_types*
        '''
        start = time.time()

        # discover schemas
        discovered_schemas = discover.discover_schemas(schema_paths)

        # resolve schemas
        valid_schemas = discover.resolve_schemas(
            discovered_schemas
        )

        end = time.time()
        logger.debug('Discover schemas run in: {}s'.format((end - start)))

        for key, value in list(valid_schemas.items()):
            logger.warning(
                'Schemas : {} : {}'.format(key, len(value))
            )

        return valid_schemas

    def reset(self):
        '''
        Empty the variables :obj:`host_type`, :obj:`host_id` and :obj:`__definitions_registry`
        '''
        self._host_types = []
        self._host_id = None
        self.__definitions_registry = {}
        self.__schemas_registry = []
        self.__plugins_registry = []

    # TODO: rename this to client_context_change_callback
    def _change_context_id(self, event):
        if event['data']['pipeline']['host_id'] != self.host_id:
            return
        context_id = event['data']['pipeline']['context_id']
        if context_id != self.context_id:
            self.context_id = context_id
