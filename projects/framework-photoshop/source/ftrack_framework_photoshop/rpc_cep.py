# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import os
import time

import ftrack_api.event.base

import ftrack_constants.framework as constants
from ftrack_utils.framework.remote import get_remote_integration_session_id


class PhotoshopRPCCEP(object):
    '''Base Photoshop remote connection for CEP based integration.'''

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
                'Successfully established connection to Photoshop {}'.format(
                    self.photoshop_version
                )
            )

    def __init__(
        self, session, client, panel_launchers, on_run_dialog_callback
    ):
        super(PhotoshopRPCCEP, self).__init__()

        self._session = session
        self._client = client
        self._panel_launchers = panel_launchers
        self.on_run_dialog_callback = on_run_dialog_callback

        self._remote_integration_session_id = None
        self._photoshop_version = None
        self._connected = False

        self.logger = logging.getLogger(__name__)

        self._initialise()

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
            'topic={} and source.applicationId=ftrack.api.javascript '
            'and data.remote_integration_session_id={}'.format(
                constants.event.DISCOVER_REMOTE_INTEGRATION_TOPIC,
                self.remote_integration_session_id,
            )
        )
        self._subscribe_event(
            event_topic, self._on_discover_remote_integration_callback
        )

        event_topic = (
            'topic={} and source.applicationId=ftrack.api.javascript '
            'and data.remote_integration_session_id={}'.format(
                constants.event.REMOTE_INTEGRATION_RUN_DIALOG_TOPIC,
                self.remote_integration_session_id,
            )
        )
        self._subscribe_event(
            event_topic,
            lambda event: self.on_run_dialog_callback(
                event['data']['dialog_name']
            ),
        )

        if True:
            # Debug events
            def print_event(event):
                print(event)

            self._subscribe_event(
                "topic=ftrack*",
                print_event,
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
        timeout=None,
    ):
        '''
        Common method that calls the private publish method from the
        remote event manager
        '''

        if timeout is None:
            timeout = 10 * 1000

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

        publish_result = self.event_hub.publish(
            publish_event, on_reply=callback_effective
        )

        if fetch_reply:
            waited = 0
            while not self._reply_event:
                time.sleep(0.01)
                waited += 10
                if waited > timeout:  # Wait 10s for reply
                    raise Exception(
                        'Timeout waiting remote integration event reply! '
                        'Waited {}s'.format(waited / 1000)
                    )
                if waited % 1000 == 0:
                    self.logger.info(
                        "Waited {}s for {} reply".format(
                            waited / 1000, event_topic
                        )
                    )
            return self._reply_event['data']

        return publish_result

    def _append_context_data(self, data):
        '''Append and return context data to event payload *data*'''
        context_id = self.client.context_id
        task = self.session.query('Task where id={}'.format(context_id)).one()
        data['context_id'] = context_id
        data['context_name'] = task['name']
        data['context_type'] = task['type']['name']
        data['context_path'] = ' / '.join(
            [d["name"] for d in task["link"][:-1]]
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
        self.logger.info("Checking if remote integration is still alive...")

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
                'Got reply for integration discovery response event: {}'.format(
                    collected_event
                )
            )
            return True
        except Exception as e:
            self.logger.exception(e)
            return False
