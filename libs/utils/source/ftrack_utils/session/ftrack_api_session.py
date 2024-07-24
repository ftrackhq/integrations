# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import ftrack_api
import logging

from ftrack_utils.event_hub import EventHubThread

logger = logging.getLogger('ftrack_utils:session')


def create_event_hub_thread(session):
    '''Create an event hub thread for the session.'''

    if not session.event_hub.connected:
        raise Exception(
            'Session event hub is not connected.Please make sure to connect the event hub before creating the event hub thread. Example: session.event_hub.connect()'
        )

    event_hub_thread = get_event_hub_thread(session)

    if not event_hub_thread:
        event_hub_thread = EventHubThread(session)
    if not event_hub_thread.is_alive():
        event_hub_thread.start()

    return event_hub_thread


def get_event_hub_thread(session):
    '''
    Get the event hub thread for the session.
    '''
    if not session.event_hub.connected:
        raise Exception(
            'Session event hub is not connected.Please make sure to connect the event hub before creating the event hub thread. Example: session.event_hub.connect()'
        )

    event_hub_thread = None
    for thread in threading.enumerate():
        if isinstance(thread, EventHubThread) and thread._session == session:
            if thread.name == str(hash(session)):
                event_hub_thread = thread
                break

    return event_hub_thread


def create_api_session(auto_connect_event_hub=True):
    '''Create an API session and an EventHubThread if auto_connect_event_hub is True.'''

    session = ftrack_api.Session(auto_connect_event_hub=auto_connect_event_hub)

    if auto_connect_event_hub:
        event_hub_thread = None
        while not session.event_hub.connected:
            # TODO: double check this to try to find a nicer way to do it.
            session.event_hub.connect()
        try:
            event_hub_thread = create_event_hub_thread(session)
        except Exception as error:
            logger.error(f'Failed to create event hub thread: {error}')
        if event_hub_thread:
            logger.debug(
                f'Event hub thread succesfully crerated {event_hub_thread}'
            )

    return session
