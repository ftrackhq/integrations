# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

from ftrack_constants.event import (
    FTRACK_ACTION_DISCOVER_TOPIC,
    FTRACK_ACTION_LAUNCH_TOPIC,
)


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
    if not discover_callback:
        discover_callback = partial(
            default_discover_action_callback, action_name, label, subscriber_id
        )

    discover_event_topic = f'{FTRACK_ACTION_DISCOVER_TOPIC} and source.user.username={session.api_user}'
    discover_subscribe_id = session.event_hub.subscribe(
        'topic={}'.format(discover_event_topic), discover_callback
    )

    launch_event_topic = f'{FTRACK_ACTION_LAUNCH_TOPIC} and data.action_name={action_name} and source.user.username={session.api_user} and data.subscriber_id={subscriber_id}'
    launch_subscribe_id = session.event_hub.subscribe(
        'topic={}'.format(launch_event_topic), launch_callback
    )

    return discover_subscribe_id, launch_subscribe_id
