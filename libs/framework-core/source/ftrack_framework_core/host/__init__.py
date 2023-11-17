# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import uuid
import logging
import socket
import os

from functools import partial

import ftrack_constants.framework as constants

from ftrack_framework_core.asset import FtrackObjectManager
from ftrack_framework_core.log.log_item import LogItem
from ftrack_framework_core.log import LogDB

from ftrack_utils.decorators import with_new_session

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

    # noinspection SpellCheckingInspection
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

    # noinspection SpellCheckingInspection
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
    def tool_configs(self):
        '''
        Returns filtered tool_configs`
        '''
        compatible_tool_configs = {}
        for tool_config in self.registry.tool_configs:
            content = tool_config['extension']
            if str(content.get('host_type')) in self.host_types:
                if (
                    content['config_type']
                    not in compatible_tool_configs.keys()
                ):
                    compatible_tool_configs[content['config_type']] = []
                compatible_tool_configs[content['config_type']].append(content)

        return compatible_tool_configs

    @property
    def registry(self):
        '''Return registry object'''
        return self._registry

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
        self._registry = registry
        self._ftrack_object_manager = None

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

    def _client_context_change_callback(self, event):
        '''Callback when the client has changed context'''
        context_id = event['data']['context_id']
        if context_id != self.context_id:
            self.context_id = context_id

    # Run
    @with_new_session
    def run_tool_config_callback(self, event, session=None):
        '''
        Runs the data with the defined engine type of the given *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run`
        '''

        tool_config_reference = event['data']['tool_config_reference']
        user_options = event['data']['user_options']

        for _tool_config in self.tool_configs:
            if _tool_config['reference'] == tool_config_reference:
                tool_config = _tool_config
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
            engine_registry = self.registry.get(
                name=engine_name, extension_type='engine'
            )[0]
            engine_instance = engine_registry['extension'](
                self.registry,
                session,
                on_plugin_executed=self.on_plugin_executed_callback,
            )
        except Exception:
            raise Exception(
                'No engine with name "{}" found'.format(engine_name)
            )

        try:
            engine_result = engine_instance.execute_engine(
                tool_config['engine'], user_options
            )

        except Exception as error:
            raise Exception(
                'Error appear when executing engine: {} from {}.'
                '\n Error: {}'.format(
                    tool_config['engine'], engine_name, error
                )
            )
        return engine_result

    def on_plugin_executed_callback(self, plugin_info):
        log_item = LogItem(plugin_info)
        self.logs.add_log_item(self.id, log_item)
        # Publish the event to notify client
        self.event_manager.publish.host_log_item_added(self.id, log_item)
