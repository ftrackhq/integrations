# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import threading

import logging
import ftrack_api
import ftrack_constants.framework as constants
import uuid
import time

logger = logging.getLogger(__name__)


class _EventHubThread(threading.Thread):
    '''Listen for events from ftrack's event hub.'''

    def __repr__(self):
        return "<{0}:{1}>".format(self.__class__.__name__, self.name)

    def __init__(self, session):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        _name = str(hash(session))
        super(_EventHubThread, self).__init__(name=_name)
        self.logger.debug('Name set for the thread: {}'.format(_name))
        self._session = session

    def start(self):
        '''Start thread for *_session*.'''
        self.logger.debug(
            'starting event hub thread for session {}'.format(self._session)
        )
        super(_EventHubThread, self).start()

    def run(self):
        '''Listen for events.'''
        self.logger.debug(
            'hub thread started for session {}'.format(self._session)
        )
        self._session.event_hub.wait()


class EventManager(object):
    '''Manages the events handling.'''

    def __repr__(self):
        return '<EventManager:{}:{}>'.format(self.mode, self.id)

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    @property
    def id(self):
        return uuid.uuid4().hex

    @property
    def session(self):
        return self._session

    @property
    def remote(self):
        '''Return the remote variant of the event manager'''
        return self._remote_event_manager

    @property
    def connected(self):
        _connected = False
        try:
            _connected = self.session.event_hub.connected
        except Exception as e:
            self.logger.error(
                "Error checking event hub connected {}".format(e)
            )
        return _connected

    @property
    def mode(self):
        return self._mode

    @property
    def publish(self):
        '''
        Property to call the Publish class with all the predefined events used
        in the framework
        '''
        return self._publish_instance

    @property
    def subscribe(self):
        '''
        Property to call the Subscribe class with all the predefined events used
        in the framework
        '''
        return self._subscribe_instance

    def _connect(self):
        # If is not already connected, connect to event hub.
        while not self.connected:
            self.session.event_hub.connect()

    def _wait(self):
        for thread in threading.enumerate():
            if thread.getName() == str(hash(self.session)):
                self._event_hub_thread = thread
                break
        if not self._event_hub_thread:
            # self.logger.debug('Initializing new hub thread {}'.format(self))
            self._event_hub_thread = _EventHubThread(self.session)

        if not self._event_hub_thread.is_alive():
            # self.logger.debug('Starting new hub thread for {}'.format(self))
            self._event_hub_thread.start()

    def __init__(
        self,
        session,
        mode=constants.event.LOCAL_EVENT_MODE,
        remote_session=None,
    ):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_hub_thread = None
        self._mode = mode
        self._session = session
        if mode == constants.event.REMOTE_EVENT_MODE:
            # TODO: Bring this back when API event hub properly can differentiate between local and remote mode
            self._connect()
            self._wait()
        elif remote_session:
            # Create a remote event manager to be able to publish events over server
            # TODO: Remove when API event hub properly can differentiate between local and remote mode
            self._remote_event_manager = EventManager(
                session=remote_session, mode=constants.event.REMOTE_EVENT_MODE
            )

        # Initialize Publish and subscribe classes to be able to provide
        # predefined events.
        self._publish_instance = Publish(self)
        self._subscribe_instance = Subscribe(self)

        # self.logger.debug('Initialising {}'.format(self))

    def _publish(self, event, callback=None, mode=None):
        '''Emit *event* and provide *callback* function, in local or remote *mode*.'''

        mode = mode or self.mode

        if mode is constants.event.LOCAL_EVENT_MODE:
            result = self.session.event_hub.publish(
                event,
                synchronous=True,
            )

            if result:
                result = result

            # Mock async event reply.
            new_event = ftrack_api.event.base.Event(
                topic='ftrack.meta.reply',
                data=result,
                in_reply_to_event=event['id'],
            )

            if callback:
                callback(new_event)

            return result

        else:
            self.session.event_hub.publish(event, on_reply=callback)

    def _subscribe(self, topic, callback):
        subscribe_id = self.session.event_hub.subscribe(
            'topic={}'.format(topic), callback
        )
        return subscribe_id

    def available_framework_events(self):
        pass


class Publish(object):
    '''Class with all the events published by the framework'''

    @property
    def event_manager(self):
        return self._event_manager

    def __init__(self, event_manager):
        super(Publish, self).__init__()
        self._event_manager = event_manager

    def _publish_event(self, event_topic, data, callback, mode=None):
        '''
        Common method that calls the private publish method from the
        event manager
        '''
        publish_event = ftrack_api.event.base.Event(
            topic=event_topic, data=data
        )
        publish_result = self.event_manager._publish(
            publish_event, callback=callback, mode=mode
        )
        return publish_result

    def _publish_remote_event(
        self, event_topic, data, callback, fetch_reply=False
    ):
        '''
        Common method that calls the private publish method from the
        remote event manager
        '''
        publish_event = ftrack_api.event.base.Event(
            topic=event_topic, data=data
        )

        # TODO: Make this thread safe in case multiple calls arrive here at the same time
        self._reply_event = None

        def default_callback(event):
            if callback:
                callback(event)
            self._reply_event = event

        if fetch_reply:
            callback_effective = default_callback
        else:
            callback_effective = callback

        # TODO: _publish does not return anything, so we shouldn't return the result
        publish_result = self.event_manager.remote._publish(
            publish_event, callback=callback_effective
        )

        if fetch_reply:
            waited = 0
            while not self._reply_event:
                time.sleep(0.01)
                waited += 10
                # TODO: Move this timeout to property that can be set on event manager init
                if waited > 10 * 1000:  # Wait 10s for reply
                    raise Exception(
                        'Timeout waiting remote integration event reply! '
                        'Waited {}s'.format(waited / 1000)
                    )
                if waited % 1000 == 0:
                    logger.info(
                        "Waited {}s for {} reply".format(
                            waited / 1000, event_topic
                        )
                    )
            return self._reply_event['data']

        return publish_result

    def discover_host(self, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_HOST_TOPIC`
        '''

        data = None
        event_topic = constants.event.DISCOVER_HOST_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_run_tool_config(self, host_id, tool_config, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_TOOL_CONFIG_TOPIC`
        '''
        data = {'host_id': host_id, 'tool_config': tool_config}
        event_topic = constants.event.HOST_RUN_TOOL_CONFIG_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_run_plugin(
        self,
        host_id,
        plugin_config,
        engine_name,
        plugin_ui_id=None,
        plugin_store=None,
        callback=None,
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_PLUGIN_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'plugin_config': plugin_config,
            'engine_name': engine_name,
            'plugin_ui_id': plugin_ui_id,
            'plugin_store': plugin_store,
        }
        event_topic = constants.event.HOST_RUN_PLUGIN_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_context_changed(self, host_id, context_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_CONTEXT_CHANGED_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'context_id': context_id,
        }
        event_topic = constants.event.HOST_CONTEXT_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_context_changed(self, host_id, context_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_CONTEXT_CHANGED_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'context_id': context_id,
        }
        event_topic = constants.event.CLIENT_CONTEXT_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def notify_plugin_progress_client(self, plugin_info, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.NOTIFY_PLUGIN_PROGRESS_TOPIC`
        '''
        event_topic = constants.event.NOTIFY_PLUGIN_PROGRESS_TOPIC
        return self._publish_event(event_topic, plugin_info, callback)

    def notify_tool_config_progress_client(
        self,
        host_id,
        step_type,
        step_name,
        stage_name,
        plugin_name,
        total_plugins,
        current_plugin_index,
        status,
        callback=None,
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.NOTIFY_TOOL_CONFIG_PROGRESS_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'step_type': step_type,
            'step_name': step_name,
            'stage_name': stage_name,
            'plugin_name': plugin_name,
            'total_plugins': total_plugins,
            'current_plugin_index': current_plugin_index,
            'status': status,
        }

        event_topic = constants.event.NOTIFY_TOOL_CONFIG_PROGRESS_TOPIC
        return self._publish_event(event_topic, data, callback)

    def host_log_item_added(self, host_id, log_item, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_LOG_ITEM_ADDED_TOPIC`
        '''
        data = {
            'host_id': host_id,
            'log_item': log_item,
        }

        event_topic = constants.event.HOST_LOG_ITEM_ADDED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_signal_context_changed(self, client_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC`
        '''
        data = {
            'client_id': client_id,
        }

        event_topic = constants.event.CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_signal_hosts_discovered(self, client_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC`
        '''
        data = {
            'client_id': client_id,
        }

        event_topic = constants.event.CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_signal_host_changed(self, client_id, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC`
        '''
        data = {
            'client_id': client_id,
        }

        event_topic = constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_notify_run_plugin_result(
        self, client_id, plugin_info, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_RUN_PLUGIN_RESULT_TOPIC`
        '''
        data = {
            'client_id': client_id,
            'plugin_info': plugin_info,
        }

        event_topic = constants.event.CLIENT_NOTIFY_RUN_PLUGIN_RESULT_TOPIC
        return self._publish_event(event_topic, data, callback)

    def client_notify_run_tool_config_result(
        self, client_id, tool_config_result, callback=None
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_RUN_TOOL_CONFIG_RESULT_TOPIC`
        '''
        data = {
            'client_id': client_id,
            'tool_config_result': tool_config_result,
        }

        event_topic = (
            constants.event.CLIENT_NOTIFY_RUN_TOOL_CONFIG_RESULT_TOPIC
        )
        return self._publish_event(event_topic, data, callback)

    def client_notify_log_item_added(self, client_id, log_item, callback=None):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC`
        '''
        data = {
            'client_id': client_id,
            'log_item': log_item,
        }

        event_topic = constants.event.CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC
        return self._publish_event(event_topic, data, callback)

    def discover_remote_integration(
        self, integration_session_id, callback=None, fetch_reply=False
    ):
        '''
        Publish a remote event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_REMOTE_INTEGRATION_TOPIC`
        supplying *integration_session_id*, calling *callback* with reply. If *fetch_reply* is
        True, the reply is awaited and returned.
        '''
        data = {
            'integration_session_id': integration_session_id,
        }

        event_topic = constants.event.DISCOVER_REMOTE_INTEGRATION_TOPIC
        return self._publish_remote_event(
            event_topic, data, callback, fetch_reply=fetch_reply
        )

    def remote_integration_context_data(
        self,
        integration_session_id,
        context_id,
        task_name,
        task_type_name,
        context_path,
        thumbnail_url,
        project_id,
        panel_launchers,
        callback=None,
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC`
        supplying *integration_session_id*, context data and panel launcher definitions.
        '''
        data = {
            'integration_session_id': integration_session_id,
            'context_id': context_id,
            'context_name': task_name,
            'context_type': task_type_name,
            'context_path': context_path,
            'context_thumbnail': thumbnail_url,
            'project_id': project_id,
            'panel_launchers': panel_launchers,
        }

        event_topic = constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC
        return self._publish_remote_event(event_topic, data, callback)

    def remote_integration_rpc(
        self,
        integration_session_id,
        function_name,
        args=None,
        callback=None,
        fetch_reply=False,
    ):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.REMOTE_INTEGRATION_RPC_TOPIC`
        supplying *integration_session_id*, to run remote *function_name* with
        arguments in *args* list, calling *callback* providing the reply.

        If *fetch_reply* is True, the reply is awaited and returned.
        '''
        data = {
            'integration_session_id': integration_session_id,
            'function_name': function_name,
            'args': args or [],
        }

        event_topic = constants.event.REMOTE_INTEGRATION_RPC_TOPIC
        return self._publish_remote_event(
            event_topic, data, callback, fetch_reply=fetch_reply
        )


class Subscribe(object):
    '''Class with all the events subscribed by the framework'''

    @property
    def event_manager(self):
        return self._event_manager

    def __init__(self, event_manager):
        super(Subscribe, self).__init__()
        self._event_manager = event_manager

    def _subscribe_event(self, event_topic, callback):
        '''Common method that calls the private subscribe method from the event manager'''
        return self.event_manager._subscribe(event_topic, callback=callback)

    def _subscribe_remote_event(self, event_topic, callback):
        '''Common method that calls the private subscribe method from the event manager'''
        return self.event_manager.remote._subscribe(
            event_topic, callback=callback
        )

    def discover_host(self, callback):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_HOST_TOPIC`
        '''
        topic = constants.event.DISCOVER_HOST_TOPIC
        return self._subscribe_event(topic, callback)

    def host_run_tool_config(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_TOOL_CONFIG_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_RUN_TOOL_CONFIG_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_run_plugin(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_RUN_PLUGIN_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_RUN_PLUGIN_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_context_changed(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_CONTEXT_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_CONTEXT_CHANGED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_context_changed(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_CONTEXT_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.CLIENT_CONTEXT_CHANGED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def notify_plugin_progress_client(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.NOTIFY_PLUGIN_PROGRESS_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.NOTIFY_PLUGIN_PROGRESS_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def notify_tool_config_progress_client(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.NOTIFY_TOOL_CONFIG_PROGRESS_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.NOTIFY_TOOL_CONFIG_PROGRESS_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def host_log_item_added(self, host_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.HOST_LOG_ITEM_ADDED_TOPIC`
        '''
        event_topic = '{} and data.host_id={}'.format(
            constants.event.HOST_LOG_ITEM_ADDED_TOPIC, host_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_signal_context_changed(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_signal_hosts_discovered(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_signal_host_changed(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_SIGNAL_HOST_CHANGED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_notify_run_plugin_result(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_RUN_PLUGIN_RESULT_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_NOTIFY_RUN_PLUGIN_RESULT_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def client_notify_run_tool_config_result(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_RUN_TOOL_CONFIG_RESULT_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_NOTIFY_RUN_TOOL_CONFIG_RESULT_TOPIC,
            client_id,
        )
        return self._subscribe_event(event_topic, callback)

    def client_notify_log_item_added(self, client_id, callback=None):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC`
        '''
        event_topic = '{} and data.client_id={}'.format(
            constants.event.CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC, client_id
        )
        return self._subscribe_event(event_topic, callback)

    def discover_remote_integration(
        self, integration_session_id, callback=None
    ):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.DISCOVER_REMOTE_INTEGRATION_TOPIC`
        and *integration_session_id*
        '''
        event_topic = (
            '{} and source.applicationId=ftrack.api.javascript '
            'and data.integration_session_id={}'.format(
                constants.event.DISCOVER_REMOTE_INTEGRATION_TOPIC,
                integration_session_id,
            )
        )
        return self._subscribe_remote_event(event_topic, callback)

    def remote_integration_run_dialog(
        self, integration_session_id, callback=None
    ):
        '''
        Subscribe to an event with topic
        :const:`~ftrack_framework_core.constants.event.REMOTE_INTEGRATION_RUN_DIALOG_TOPIC`
        and *integration_session_id*
        '''
        event_topic = (
            '{} and source.applicationId=ftrack.api.javascript '
            'and data.integration_session_id={}'.format(
                constants.event.REMOTE_INTEGRATION_RUN_DIALOG_TOPIC,
                integration_session_id,
            )
        )
        return self._subscribe_remote_event(event_topic, callback)
