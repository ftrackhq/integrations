# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import os

from Qt import QtWidgets

import ftrack_api.event.base

import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_remote_integration_session_id


class PhotoshopRPCCEP(object):
    '''Base Photoshop remote connection for CEP based integration.'''

    # Connection should be a singleton accessible also during plugin execution
    _instance = None

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
    def photoshop_version(self):
        '''Return Photoshop version.'''
        return self._photoshop_version

    @photoshop_version.setter
    def photoshop_version(self, value):
        '''Set Photoshop version to *value*.'''
        self._photoshop_version = value

    @property
    def remote_integration_session_id(self):
        '''Return remote integration session ID.'''
        return self._remote_integration_session_id

    @remote_integration_session_id.setter
    def remote_integration_session_id(self, value):
        '''Set remote integration session ID to *value*.'''
        self._remote_integration_session_id = value

    @property
    def on_run_dialog_callback(self):
        '''Return callback for run dialog event.'''
        return self._on_run_dialog_callback

    @on_run_dialog_callback.setter
    def on_run_dialog_callback(self, value):
        '''Set callback for run dialog event to *value*.'''
        self._on_run_dialog_callback = value

    @property
    def connected(self):
        '''Return True if connected to Photoshop.'''
        return self._connected

    @connected.setter
    def connected(self, value):
        '''Set connected state to *value*.'''
        self._connected = value
        if self._connected:
            self.logger.info(
                f'Successfully established connection to Photoshop {self.photoshop_version}'
            )

    def __init__(
        self, session, client, panel_launchers, on_run_dialog_callback
    ):
        super(PhotoshopRPCCEP, self).__init__()

        # Store reference to self in class variable
        PhotoshopRPCCEP._instance = self

        self._session = session
        self._client = client
        self._panel_launchers = panel_launchers
        self.on_run_dialog_callback = on_run_dialog_callback

        self._remote_integration_session_id = None
        self._photoshop_version = None
        self._connected = False

        self.logger = logging.getLogger(__name__)

        self._initialise()

    @staticmethod
    def instance():
        '''Return the singleton instance, checks if it is initialised and connected.'''
        assert PhotoshopRPCCEP._instance, 'Photoshop RPC not created!'
        assert (
            PhotoshopRPCCEP._instance.connected
        ), 'Photoshop not connected, please keep panel open while integration is working!'

        return PhotoshopRPCCEP._instance

    def _initialise(self):
        '''Initialise the Photoshop connection'''

        self.photoshop_version = os.environ.get('FTRACK_PHOTOSHOP_VERSION')
        assert (
            self.photoshop_version
        ), 'Photoshop integration requires FTRACK_PHOTOSHOP_VERSION passed as environment variable!'

        self.remote_integration_session_id = (
            get_remote_integration_session_id()
        )
        assert (
            self.remote_integration_session_id
        ), 'Photoshop integration requires FTRACK_REMOTE_INTEGRATION_SESSION_ID passed as environment variable!'

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
            lambda event: self.on_run_dialog_callback(
                event['data']['dialog_name'],
                event['data']['tool_configs'],
            ),
        )

        self.logger.info(
            f'Created Photoshop {self.photoshop_version} connection (session id: {self.remote_integration_session_id})'
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
            app = QtWidgets.QApplication.instance()
            while not reply_event:
                app.processEvents()
                self.session.event_hub.wait(0.01)
                waited += 10
                if waited > timeout:
                    raise Exception(
                        'Timeout waiting remote integration event reply! '
                        f'Waited {waited / 1000}s'
                    )
                if waited % 1000 == 0:
                    self.logger.info(
                        f'Waited {waited / 1000}s for {event_topic} reply'
                    )
            return reply_event['data']

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

    # Lifecycle methods

    def check_responding(self):
        '''Check if Photoshop is alive, send context data'''
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

        self.logger.debug(f'Running Photoshop RPC call: {data}')

        event_topic = constants.event.REMOTE_INTEGRATION_RPC_TOPIC

        result = self._publish_event(
            event_topic, data, callback, fetch_reply=fetch_reply
        )['result']

        self.logger.debug(f'Got Photoshop RPC response: {result}')

        return result
