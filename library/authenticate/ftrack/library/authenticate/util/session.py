# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
from ftrack_api import Session
import logging
import time

from .event_hub_thread import EventHubThread

# Configure logging
logging.basicConfig(level=logging.INFO)


def create_event_hub_thread(session):
    """Create an event hub thread for the session."""

    if not session.event_hub.connected:
        raise Exception(
            "Session event hub is not connected. Please make sure to connect the event hub before creating the event hub thread. Example: session.event_hub.connect()"
        )

    event_hub_thread = get_event_hub_thread(session)

    if not event_hub_thread:
        event_hub_thread = EventHubThread(session)
    if not event_hub_thread.is_alive():
        event_hub_thread.start()

    return event_hub_thread


def get_event_hub_thread(session):
    """
    Get the event hub thread for the session.
    """
    if not session.event_hub.connected:
        raise Exception(
            "Session event hub is not connected. Please make sure to connect the event hub before creating the event hub thread. Example: session.event_hub.connect()"
        )

    event_hub_thread = None
    for thread in threading.enumerate():
        if isinstance(thread, EventHubThread) and thread._session == session:
            if thread.name == str(hash(session)):
                event_hub_thread = thread
                break

    return event_hub_thread


def wait_for_event_hub_connection(session, timeout=30, poll_interval=0.5):
    time.sleep(poll_interval)
    start_time = time.time()
    while not session.event_hub.connected:
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Failed to connect to the event hub within the timeout period or {timeout}."
            )
        logging.debug("retrying connection")
        session.event_hub.connect()
        time.sleep(poll_interval)


def create_api_session(server_url, api_key, api_user, auto_connect_event_hub=True):
    """Create an API session and an EventHubThread if auto_connect_event_hub is True."""

    session = Session(
        server_url, api_key, api_user, auto_connect_event_hub=auto_connect_event_hub
    )

    if auto_connect_event_hub:
        event_hub_thread = None
        try:
            wait_for_event_hub_connection(session)
        except Exception as error:
            logging.error(f"Failed to connect to event hub: {error}")
        try:
            event_hub_thread = create_event_hub_thread(session)
        except Exception as error:
            logging.error(f"Failed to create event hub thread: {error}")
        if event_hub_thread:
            logging.debug(f"Event hub thread succesfully crerated {event_hub_thread}")

    return session
