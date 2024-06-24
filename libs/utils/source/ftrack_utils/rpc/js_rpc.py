# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import os

import ftrack_api.event.base

import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_remote_integration_session_id


class JavascriptRPC(object):
    '''Base RPC implementation for standalone integrations communicating
    over the ftrack event hub with a Javascript DCC.'''

    # Connection should be a singleton accessible also during plugin execution
    _instance = None

    @property
    def dcc_name(self):
        '''Return DCC name.'''
        return self._dcc_name

    @property
    def session(self):
        return self._session

    @property
    def event_hub(self):
        '''Return event hub.'''
        return self.session.event_hub

    @property
    def client(self):
        '''Return client.'''
        return self._client

    @property
    def dcc_version(self):
        '''Return DCC version.'''
        return self._dcc_version

    @dcc_version.setter
    def dcc_version(self, value):
        '''Set DCC version to *value*.'''
        self._dcc_version = value

    @property
    def remote_integration_session_id(self):
        '''Return remote integration session ID.'''
        return self._remote_integration_session_id

    @remote_integration_session_id.setter
    def remote_integration_session_id(self, value):
        '''Set remote integration session ID to *value*.'''
        self._remote_integration_session_id = value

    @property
    def on_run_tool_callback(self):
        '''Return callback for run dialog event.'''
        return self._on_run_tool_callback

    @property
    def on_connected_callback(self):
        '''Return callback to call upon a new connection.'''
        return self._on_connected_callback

    @property
    def process_events_callback(self):
        '''Return callback for processing events.'''
        return self._process_events_callback

    @property
    def connected(self):
        '''Return True if connected to DCC.'''
        return self._connected

    @connected.setter
    def connected(self, value):
        '''Set connected state to *value*.'''
        self._connected = value
        if self._connected:
            self.logger.info(
                f'Successfully established connection to DCC {self.dcc_version}'
            )

    def __init__(
        self,
        dcc_name,
        session,
        client,
        panel_launchers,
        on_connected_callback,
        on_run_tool_callback,
        process_events_callback,
    ):
        '''
        Initialise the event hub Javascript RPC connection

        :param dcc_name: The name of the DCC; 'photoshop', 'premiere', etc.
        :param session:
        :param client: The client instance
        :param panel_launchers: List of tools that should be sent to DCC on connection
        :param on_connected_callback: Callback for connected event
        :param on_run_tool_callback: Callback for run dialog event
        :param process_events_callback: Callback for processing events while waiting for RCP event reply
        '''
        super(JavascriptRPC, self).__init__()

        # Store reference to self in class variable
        JavascriptRPC._instance = self

        self._dcc_name = dcc_name
        self._session = session
        self._client = client
        self._panel_launchers = panel_launchers

        self._on_connected_callback = on_connected_callback
        self._on_run_tool_callback = on_run_tool_callback
        self._process_events_callback = process_events_callback

        self._remote_integration_session_id = None
        self._dcc_version = None
        self._connected = False

        self.logger = logging.getLogger(__name__)

        self._initialise()

    @staticmethod
    def instance():
        '''Return the singleton instance, checks if it is initialised and connected.'''
        assert JavascriptRPC._instance, 'Javascript RPC instance not created!'
        assert (
            JavascriptRPC._instance.connected
        ), 'DCC not connected, please keep panel open while integration is working!'

        return JavascriptRPC._instance

    def _initialise(self):
        '''Initialise the DCC RPC connection'''
        env_name = f'FTRACK_{self.dcc_name.upper()}_VERSION'
        self.dcc_version = os.environ.get(env_name)
        assert (
            self.dcc_version
        ), f'{self.dcc_name.title()} integration requires {env_name} passed as environment variable!'

        self.remote_integration_session_id = (
            get_remote_integration_session_id()
        )
        assert self.remote_integration_session_id, (
            f'{self.dcc_name.title()} integration requires FTRACK_REMOTE_INTEGRATION_SESSION_ID passed as environment'
            f' variable!'
        )

        event_topic = (
            f'topic={constants.event.DISCOVER_REMOTE_INTEGRATION_TOPIC} and source.applicationId=ftrack.api.javascript '
            f'and data.remote_integration_session_id={self.remote_integration_session_id}'
        )
        self._subscribe_event(
            event_topic, self._on_discover_remote_integration_callback
        )

        event_topic = (
            f'topic={constants.event.REMOTE_INTEGRATION_RUN_DIALOG_TOPIC} and source.applicationId=ftrack.api.javascript '
            f'and data.remote_integration_session_id={self.remote_integration_session_id}'
        )
        self._subscribe_event(
            event_topic,
            lambda event: self.on_run_tool_callback(
                event['data']['name'],
                event['data']['dialog_name'],
                event['data']['options'],
            ),
        )

        self.logger.info(
            f'Created {self.dcc_name} {self.dcc_version} connection (session id: {self.remote_integration_session_id})'
        )

    # Event hub methods

    def _subscribe_event(self, event_topic, callback):
        self.event_hub.subscribe(event_topic, callback)

    def _publish_event(
        self,
        event_topic,
        data,
        callback=None,
        fetch_reply=False,
        timeout=10 * 1000,
    ):
        '''
        Common method that calls the private publish method from the
        remote event manager
        '''

        publish_event = ftrack_api.event.base.Event(
            topic=event_topic, data=data
        )

        reply_event = None

        def default_callback(event):
            if callback:
                callback(event)
            nonlocal reply_event
            reply_event = event

        if fetch_reply:
            callback_effective = default_callback
        else:
            callback_effective = callback

        publish_result = self.event_hub.publish(
            publish_event, on_reply=callback_effective
        )

        if fetch_reply:
            waited = 0
            while not reply_event:
                if self.process_events_callback:
                    self.process_events_callback()
                self.session.event_hub.wait(0.01)
                waited += 10
                if waited > timeout:
                    raise Exception(
                        'Timeout waiting for remote integration event reply - '
                        ' CEP plugin installed and functioning?'
                        f'Waited {waited / 1000}s'
                    )
                if waited % 1000 == 0:
                    self.logger.info(
                        f'Waited {waited / 1000}s for {event_topic} reply'
                    )
            retval = reply_event['data']
            if 'error_message' in retval:
                raise Exception(
                    f'An error occurred while publishing event {event_topic}: {retval["error_message"]}'
                )
            return retval
        return publish_result

    def _append_context_data(self, data):
        '''Append and return context data to event payload *data*'''
        context_id = self.client.context_id
        task = self.session.query(f'Task where id={context_id}').one()
        data['context_id'] = context_id
        data['context_name'] = task['name']
        data['context_type'] = task['type']['name']
        data['context_path'] = ' / '.join(
            [d['name'] for d in task['link'][:-1]]
        )
        data['context_thumbnail'] = task['thumbnail_url']['url']
        data['project_id'] = task['project_id']
        return data

    def _on_discover_remote_integration_callback(self, event):
        '''Callback for discover_remote_integration *event*, sends
        back context data'''
        if not self.connected:
            self.connected = True

        self._publish_event(
            constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC,
            self._append_context_data(
                {
                    'remote_integration_session_id': self.remote_integration_session_id,
                    'panel_launchers': self._panel_launchers,
                }
            ),
        )
        if self.on_connected_callback:
            self.on_connected_callback(event)

    # Lifecycle methods

    def check_responding(self):
        '''Check if DCC is alive, send context data'''
        self.logger.info('Checking if remote integration is still alive...')

        try:
            # Send event and wait for reply sync.
            collected_event = self._publish_event(
                constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC,
                self._append_context_data(
                    {
                        'remote_integration_session_id': self.remote_integration_session_id
                    }
                ),
                fetch_reply=True,
            )
            self.logger.info(
                f'Got reply for integration discovery response event: {collected_event}'
            )
            return True
        except Exception as e:
            self.logger.exception(e)
            return False

    # RPC methods

    def rpc(self, function_name, args=None, callback=None, fetch_reply=True):
        '''
        Publish an event with topic
        :const:`~ftrack_framework_core.constants.event.REMOTE_INTEGRATION_RPC_TOPIC`
        , to run remote *function_name* with arguments in *args* list, calling
        *callback* providing the reply (async) or
        awaiting and fetching the reply if *fetch_reply* is True (sync, default).

        '''

        assert not (callback and fetch_reply), (
            'Cannot use callback and fetch reply ' 'at the same time!'
        )

        data = {
            'remote_integration_session_id': self.remote_integration_session_id,
            'function_name': function_name,
            'args': args or [],
        }

        self.logger.debug(f'Running {self.dcc_name.title()} RPC call: {data}')

        event_topic = constants.event.REMOTE_INTEGRATION_RPC_TOPIC

        result = self._publish_event(
            event_topic, data, callback, fetch_reply=fetch_reply
        )['result']

        self.logger.debug(
            f'Got {self.dcc_name.title()} RPC response: {result}'
        )

        return result
