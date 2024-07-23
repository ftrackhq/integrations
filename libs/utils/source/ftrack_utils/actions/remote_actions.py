# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import threading
from functools import partial

from ftrack_constants.event import (
    FTRACK_ACTION_DISCOVER_TOPIC,
    FTRACK_ACTION_LAUNCH_TOPIC,
)

from ftrack_utils.event_hub import EventHubThread

logger = logging.getLogger('ftrack_utils:actions:remote_actions')


def default_discover_action_callback(action_name, label, subscriber_id, event):
    '''Discover *event*.'''
    return {
        'items': [
            {
                'action_name': action_name,
                'label': label,
                'subscriber_id': subscriber_id,
            }
        ]
    }


def register_remote_action(
    session,
    action_name,
    label,
    subscriber_id,
    launch_callback,
    discover_callback=None,
):
    """
    Register a remote action with the given name and callbacks.

    Parameters:
        session (ftrack_api.Session): The session to use.
        action_name (str): The name of the action.
        discover_callback (callable): The callback to use for discovery.
        launch_callback (callable): The callback to use for launching.
        subscriber_id (str, optional): The subscriber id to use.

    Returns:
        None
    """
    # Check if session is connected to event hub
    if not session.event_hub.connected:
        logger.warning(
            'Session is not connected to event hub, trying to connect'
        )
        try:
            session.event_hub.connect()
        except Exception as e:
            logger.error(
                'Failed to connect to event hub, not registring actions: {}'.format(
                    e
                )
            )
            return

    # Check if already has an event hub otherwise create one
    event_hub_thread = None
    for thread in threading.enumerate():
        if isinstance(thread, EventHubThread) and thread._session == session:
            if thread.name == str(hash(session)):
                event_hub_thread = thread
                break
    if not event_hub_thread:
        event_hub_thread = EventHubThread(session)
    if not event_hub_thread.is_alive():
        event_hub_thread.start()

    # Use the default discover callback if not provided
    if not discover_callback:
        discover_callback = partial(
            default_discover_action_callback, action_name, label, subscriber_id
        )

    # Subscribe to the discover event
    discover_event_topic = f'{FTRACK_ACTION_DISCOVER_TOPIC} and source.user.username={session.api_user}'
    discover_subscribe_id = session.event_hub.subscribe(
        'topic={}'.format(discover_event_topic), discover_callback
    )

    # Subscribe to the launch event
    launch_event_topic = f'{FTRACK_ACTION_LAUNCH_TOPIC} and data.action_name={action_name} and source.user.username={session.api_user} and data.subscriber_id={subscriber_id}'
    launch_subscribe_id = session.event_hub.subscribe(
        'topic={}'.format(launch_event_topic), launch_callback
    )

    # Return discover and launch subscription ids.
    return discover_subscribe_id, launch_subscribe_id
