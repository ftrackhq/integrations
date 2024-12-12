# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import logging
import time
from typing import Optional, TYPE_CHECKING
from ftrack_api import Session
from ..helper.event_hub_thread import EventHubThread

# Configure logging
logging.basicConfig(level=logging.INFO)


def wait_for_event_hub_connection(
    session: Session, timeout: int = 30, poll_interval: float = 0.5
) -> None:
    """
    Wait until the event hub is connected, retrying if necessary.

    :param session: The session whose event hub to wait for.
    :param timeout: Maximum time to wait in seconds.
    :param poll_interval: Interval between connection attempts in seconds.
    :raises TimeoutError: If the event hub fails to connect within the timeout.
    """
    start_time = time.time()
    while not session.event_hub.connected:
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Failed to connect to the event hub within {timeout} seconds."
            )
        session.event_hub.connect()
        time.sleep(poll_interval)


def create_event_hub_thread(session: Session) -> EventHubThread:
    """
    Create or retrieve an EventHubThread for the session.

    :param session: The session for which to create or retrieve the thread.
    :return: An instance of EventHubThread.
    :raises Exception: If the session event hub is not connected.
    """
    if not session.event_hub.connected:
        raise Exception("Session event hub is not connected. Connect first.")

    thread: Optional[EventHubThread] = get_event_hub_thread(session)
    if not thread:
        thread = EventHubThread(session)
    if not thread.is_alive():
        thread.start()
    return thread


def get_event_hub_thread(session: Session) -> Optional[EventHubThread]:
    """
    Retrieve an existing EventHubThread for the session, if any.

    :param session: The session whose thread to retrieve.
    :return: An instance of EventHubThread if found, otherwise None.
    :raises Exception: If the session event hub is not connected.
    """
    if not session.event_hub.connected:
        raise Exception("Session event hub is not connected. Connect first.")

    for thread in threading.enumerate():
        if isinstance(thread, EventHubThread) and thread.session == session:
            return thread
    return None


def create_api_session(
    server_url: str, api_key: str, api_user: str, auto_connect_event_hub: bool = True
) -> Session:
    """
    Create an API session and optionally connect the event hub.

    :param server_url: URL of the server.
    :param api_key: API key for authentication.
    :param api_user: API user for authentication.
    :param auto_connect_event_hub: Whether to automatically connect the event hub.
    :return: A new Session instance.
    """
    session: Session = Session(
        server_url, api_key, api_user, auto_connect_event_hub=auto_connect_event_hub
    )
    if auto_connect_event_hub:
        try:
            wait_for_event_hub_connection(session)
            create_event_hub_thread(session)
        except Exception as e:
            logging.error(f"Failed to initialize event hub: {e}")
    return session
