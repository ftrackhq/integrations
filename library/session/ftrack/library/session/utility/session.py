# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import logging
import time
from ftrack_api import Session
from ..helper.event_hub_thread import EventHubThread

# Configure logging
logging.basicConfig(level=logging.INFO)


def wait_for_event_hub_connection(session, timeout=30, poll_interval=0.5):
    """Wait until the event hub is connected, retrying if necessary."""
    start_time = time.time()
    while not session.event_hub.connected:
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Failed to connect to the event hub within {timeout} seconds."
            )
        session.event_hub.connect()
        time.sleep(poll_interval)


def create_event_hub_thread(session):
    """Create or retrieve an EventHubThread for the session."""
    if not session.event_hub.connected:
        raise Exception("Session event hub is not connected. Connect first.")

    thread = get_event_hub_thread(session)
    if not thread:
        thread = EventHubThread(session)
    if not thread.is_alive():
        thread.start()
    return thread


def get_event_hub_thread(session):
    """Retrieve an existing EventHubThread for the session, if any."""

    if not session.event_hub.connected:
        raise Exception("Session event hub is not connected. Connect first.")

    for thread in threading.enumerate():
        if isinstance(thread, EventHubThread) and thread.session == session:
            return thread
    return None


def create_api_session(server_url, api_key, api_user, auto_connect_event_hub=True):
    """Create an API session and optionally connect the event hub."""
    session = Session(
        server_url, api_key, api_user, auto_connect_event_hub=auto_connect_event_hub
    )
    if auto_connect_event_hub:
        try:
            wait_for_event_hub_connection(session)
            create_event_hub_thread(session)
        except Exception as e:
            logging.error(f"Failed to initialize event hub: {e}")
    return session
