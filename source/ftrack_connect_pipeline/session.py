# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import os
import logging

import ftrack_api
import ftrack_api.exception


_shared_session = None


def destroy_shared_session():
    '''Destroy the shared session.'''
    logger = logging.getLogger('ftrack_connect:session.destroy_shared_session')
    global _shared_session

    if _shared_session:
        # Disconnect from event hub but do not unsubscribe as that will be
        # blocking and slow. Also there is no need to unsubscribe since the
        # session will not be used any more.
        try:
            _shared_session.event_hub.disconnect(False)
        except ftrack_api.exception.EventHubConnectionError as error:
            # TODO: Handle if event hub is not yet connected.
            logger.exception('Failed to disconnect from event hub')
            pass

        del _shared_session
        _shared_session = None


def get_shared_session(plugin_paths=None):
    '''Return shared ftrack_api session.'''
    global _shared_session

    if not _shared_session:
        # Create API session using credentials as stored by the application
        # when logging in.
        _shared_session = ftrack_api.Session(
            auto_connect_event_hub=False,
            server_url=os.environ['FTRACK_SERVER'],
            api_key=os.environ['FTRACK_APIKEY'],
            api_user=os.environ['LOGNAME'],
            plugin_paths=plugin_paths
        )

        # if is not connected, connect to event hub
        if not _shared_session.event_hub.connected:
            _shared_session.event_hub.connect()

    return _shared_session
