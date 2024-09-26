# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import uuid
import logging
import os

from functools import partial

from ftrack_framework_core.log.log_item import LogItem
from ftrack_framework_core.log import LogDB
from ftrack_utils.framework.config.tool import get_plugins
from ftrack_framework_core.exceptions.engine import EngineExecutionError

from ftrack_utils.decorators import (
    with_new_session,
    delegate_to_main_thread_wrapper,
)
from ftrack_utils.decorators.threading import call_directly

logger = logging.getLogger(__name__)

# TODO: this is the discover_host_reply function:
#  1. Double check if this should better be part of the host class as a method.
#  2. Rename it to discover_host_reply_callback or similar?


def provide_host_information(host_id, context_id, tool_configs, event):
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
        'context_id': context_id,
        'tool_configs': tool_configs,
    }
    # TODO: we could pass the engines as well so client knows what engines do we
    #  have available. Re-evaluate this as it might not be necessary as the engine
    #  is always given by the tool_config....
    return host_dict


class Host(object):
    '''Base class to represent a Host of the framework'''

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
        self.event_manager.unsubscribe(self._discover_host_subscribe_id)
        # Reply to discover_host_callback to clients to pass the host information
        discover_host_callback_reply = self.run_in_main_thread(
            partial(
                provide_host_information,
                self.id,
                self.context_id,
                self.tool_configs,
            )
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
    def logs(self):
        '''Returns the current logs'''
        if not self._logs:
            self._logs = LogDB(self._id)
        return self._logs

    @property
    def tool_configs(self):
        '''
        Returns filtered tool_configs`
        '''
        compatible_tool_configs = {}
        for tool_config in self.registry.tool_configs:
            content = tool_config['extension']
            if content['config_type'] not in compatible_tool_configs.keys():
                compatible_tool_configs[content['config_type']] = []
            compatible_tool_configs[content['config_type']].append(content)

        return compatible_tool_configs

    @property
    def registry(self):
        '''Return registry object'''
        return self._registry

    def __init__(
        self, event_manager, registry, run_in_main_thread_wrapper=None
    ):
        '''
        Initialise Host with instance of
        :class:`~ftrack_framework_core.event.EventManager` and extensions *registry*
        '''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # Set up the run_in_main_thread decorator
        if run_in_main_thread_wrapper:
            self.run_in_main_thread_wrapper = run_in_main_thread_wrapper
        else:
            # Using the util.call_directly function as the default method
            self.run_in_main_thread_wrapper = call_directly

        # Create the host id
        self._id = uuid.uuid4().hex

        self.logger.debug('Initializing Host {}'.format(self))

        # Reset Logs
        self._logs = None
        # Set event manager and object manager
        self._event_manager = event_manager
        self._registry = registry

        self._discover_host_subscribe_id = None

        # Subscribe to events
        self._subscribe_events()

        self.logger.debug('Host {} ready.'.format(self.id))

    # Subscribe
    def _subscribe_events(self):
        '''Host subscription events to communicate with the client'''

        # Listen to context change events for this host and its connected clients
        self.event_manager.subscribe.client_context_changed(
            self.id, self._client_context_change_callback
        )

        # Reply to discover_host_callback to client to pass the host information
        discover_host_callback_reply = self.run_in_main_thread_wrapper(
            partial(
                provide_host_information,
                self.id,
                self.context_id,
                self.tool_configs,
            )
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

        # Subscribe to run ui hook
        self.event_manager.subscribe.host_run_ui_hook(
            self.id, self.run_ui_hook_callback
        )

        # Subscribe to run ui hook
        self.event_manager.subscribe.host_verify_plugins(
            self.id, self._verify_plugins_callback
        )

    @delegate_to_main_thread_wrapper
    def _client_context_change_callback(self, event):
        '''Callback when the client has changed context'''
        context_id = event['data']['context_id']
        if context_id != self.context_id:
            self.context_id = context_id

    # Run
    @delegate_to_main_thread_wrapper
    def run_tool_config_callback(self, event):
        '''
        Runs the data with the defined engine type of the given *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        tool_config_reference = event['data']['tool_config_reference']
        client_options = event['data']['client_options']

        for typed_configs in self.tool_configs.values():
            tool_config = None
            for _tool_config in typed_configs:
                if _tool_config['reference'] == tool_config_reference:
                    tool_config = _tool_config
                    break
            if tool_config:
                break
        else:
            raise Exception(
                'Given tool config reference {} not found on registered '
                'tool_configs. \n {}'.format(
                    tool_config_reference, self.tool_configs
                )
            )
        engine_name = tool_config.get('engine_name', 'standard_engine')

        try:
            engine_registry = self.registry.get_one(
                name=engine_name, extension_type='engine'
            )
            engine_instance = engine_registry['extension'](
                self.registry,
                self.session,
                self.context_id,
                on_plugin_executed=self.on_plugin_executed_callback,
            )
        except Exception:
            raise Exception(
                'No engine with name "{}" found'.format(engine_name)
            )

        try:
            engine_instance.execute_engine(
                tool_config['engine'], client_options
            )

        except EngineExecutionError as error:
            self.logger.exception(error)
        except Exception as error:
            self.logger.exception(
                f'Un-handled error appear when executing engine: '
                f'{tool_config["engine"]} from {engine_name}.'
                f'\n Error: {error}'
            )

    def on_plugin_executed_callback(self, plugin_info):
        log_item = LogItem(plugin_info)
        self.logs.add_log_item(self.id, log_item)
        # Publish the event to notify client
        self.event_manager.publish.host_log_item_added(self.id, log_item)

    @delegate_to_main_thread_wrapper
    def run_ui_hook_callback(self, event):
        '''
        Runs the data with the defined engine type of the given *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        tool_config_reference = event['data']['tool_config_reference']
        plugin_reference = event['data']['plugin_config_reference']
        client_options = event['data']['client_options']
        payload = event['data']['payload']

        for typed_configs in self.tool_configs.values():
            tool_config = None
            for _tool_config in typed_configs:
                if _tool_config['reference'] == tool_config_reference:
                    tool_config = _tool_config
                    break
            if tool_config:
                break
        else:
            raise Exception(
                'Given tool config reference {} not found on registered '
                'tool_configs. \n {}'.format(
                    tool_config_reference, self.tool_configs
                )
            )

        engine_name = tool_config.get('engine_name', 'standard_engine')

        try:
            engine_registry = self.registry.get_one(
                name=engine_name, extension_type='engine'
            )
            engine_instance = engine_registry['extension'](
                self.registry,
                self.session,
                on_plugin_executed=partial(
                    self.on_ui_hook_executed_callback, plugin_reference
                ),
            )
        except Exception:
            raise Exception(
                'No engine with name "{}" found'.format(engine_name)
            )

        try:
            plugin_config = get_plugins(
                tool_config, filters={'reference': plugin_reference}
            )[0]
        except Exception:
            raise Exception(
                'Given plugin config reference {} not found on the '
                'tool_config {}'.format(plugin_reference, tool_config)
            )

        try:
            engine_result = engine_instance.run_ui_hook(
                plugin_config['plugin'],
                payload,
                client_options,
                reference=plugin_reference,
            )

        except Exception as error:
            raise Exception(
                'Error appear when executing engine: {} from {}.'
                '\n Error: {}'.format(
                    tool_config['engine'], engine_name, error
                )
            )
        return engine_result

    def on_ui_hook_executed_callback(self, plugin_reference, ui_hook_result):
        self.event_manager.publish.host_run_ui_hook_result(
            self.id, plugin_reference, ui_hook_result
        )

    @delegate_to_main_thread_wrapper
    def _verify_plugins_callback(self, event):
        '''
        Call the verify_plugins and return the result to the client.
        '''
        plugin_names = event['data']['plugin_names']
        return self.verify_plugins(plugin_names)

    def verify_plugins(self, plugin_names):
        '''
        Verify the given *plugin_names* are registered in the registry.
        '''
        unregistered_plugins = []
        for plugin_name in plugin_names:
            if not self.registry.get(plugin_name, extension_type='plugin'):
                unregistered_plugins.append(plugin_name)
        if unregistered_plugins:
            self.logger.error(
                f'Plugins not registered, please make sure they are in the '
                f'correct extensions path: {unregistered_plugins}'
            )
        return unregistered_plugins
