# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

from ftrack_utils.decorators import asynchronous


logger = logging.getLogger('ftrack_utils:server.send_event')


def send_event(session, action, event_name, metadata=None):
    '''Send usage event with *event_name* and *metadata*.'''

    if not isinstance(metadata, list):
        metadata = [metadata]

    payload = []
    for data in metadata:
        payload.append(
            {
                'action': action,
                'data': {
                    'type': 'event',
                    'name': event_name,
                    'metadata': data,
                },
            }
        )

    try:
        session.call(payload)

    except Exception:
        logger.exception('Failed to send event : {}'.format(event_name))


@asynchronous
def send_async_event(session, action, event_name, metadata=None):
    '''Call __send_event in a new thread.'''
    send_event(session, action, event_name, metadata)
