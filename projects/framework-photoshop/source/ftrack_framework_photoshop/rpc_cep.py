# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

import ftrack_api.event.base

import ftrack_constants.framework as constants

logger = logging.getLogger(__name__)


class PhotoshopRPC(object):
    '''Base Photoshop remote connection.'''
    
    @property
    def event_hub(self):
        '''Return event hub.'''
        return self._event_hub

    @property
    def connected(self):
        '''Return True if connected to Photoshop.'''
        return self._connected

    @connected.setter
    def connected(self, value):
        '''Set connected state to *value*.'''
        self._connected = value
        if self.connect:
            logger.info(
                'Successfully established connection to Photoshop {}'.format(
                    self.photoshop_version
                )
            )

    def __init__(self, event_hub, panel_launchers, integration_session_id, on_run_dialog_callback):
        super(PhotoshopRPC, self).__init__()

        self._event_hub = event_hub
        self._panel_launchers = panel_launchers
        self._connected = False
        self.integration_session_id = integration_session_id
        self.on_run_dialog_callback = on_run_dialog_callback

        self._initialise()

    def _initialise(self):
        '''Initialise the Photoshop connection'''

        # self.event_manager.subscribe.discover_remote_integration(
        #     get_integration_session_id(),
        #     self._on_discover_remote_integration_callback,
        # )

        event_topic = (
            'topic={} and source.applicationId=ftrack.api.javascript '
            'and data.integration_session_id={}'.format(
                constants.event.DISCOVER_REMOTE_INTEGRATION_TOPIC,
                self.integration_session_id,
            )
        )
        self.subscribe_event(
            event_topic,
            self._on_discover_remote_integration_callback    
        )

        event_topic = (
            'topic={} and source.applicationId=ftrack.api.javascript '
            'and data.integration_session_id={}'.format(
                constants.event.REMOTE_INTEGRATION_RUN_DIALOG_TOPIC,
                self.integration_session_id,
            )
        )
        return self.subscribe_event(
            event_topic,
            lambda event: self.on_run_dialog_callback(event['data']['dialog_name'])
        )

    def subscribe_event(self, event_topic, callback):
        self.event_hub.subscribe(
            event_topic, callback
        )

    def publish_event(self, event_topic, data, callback=None):
        event = ftrack_api.event.base.Event(
            topic=event_topic,
            data=data
        )
        self.event_hub.publish(
            event, on_reply=callback
        )

    def _on_discover_remote_integration_callback(self, event):
        '''Callback for discover_remote_integration *event*, sends
        back context data'''
        if not self.connected:
            self.connected = True
            logger.info("Connected to Photoshop.")

        self.publish_event(
            constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC,
            {
                'integration_session_id': self.integration_session_id,
                'panel_launchers': self._panel_launchers,
            }
        )

    def check_responding(self):
        '''Check if Photoshop is alive, send ping'''
        logger.info(
            "Checking if remote integration is still alive..."
        )
        collected_event = None
        def callback(event):
            nonlocal collected_event
            collected_event = event

        # Send event and wait for reply sync.
        self.publish_event(
            constants.event.REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC,
            {
                'integration_session_id': self.integration_session_id,
                'panel_launchers': self._panel_launchers,
            },
            callback
        )

        # Wait maximum 100 * 100ms = 10s.
        for _ in range(100):
            # Wait 100ms.
            self.event_hub.wait(0.1)
            if collected_event:
                logger.info(
                    'Got reply for integration discovery response event: {}'.format(
                        collected_event
                    )
                )

        return False
