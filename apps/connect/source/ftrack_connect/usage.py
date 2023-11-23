# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

import ftrack_connect.asynchronous


logger = logging.getLogger('ftrack_connect:usage')


def _send_event(session, event_name, metadata=None):
    '''Send usage event with *event_name* and *metadata*.'''

    if not isinstance(metadata, list):
        metadata = [metadata]

    payload = []
    for data in metadata:
        payload.append(
            {
                'action': '_track_usage',
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


@ftrack_connect.asynchronous.asynchronous
def _send_async_event(session, event_name, metadata=None):
    '''Call __send_event in a new thread.'''
    _send_event(session, event_name, metadata)


def send_event(session, event_name, metadata=None, asynchronous=True):
    '''Send usage event with *event_name* and *metadata*.

    If asynchronous is True, the event will be sent in a new thread.
    '''

    if asynchronous:
        _send_async_event(session, event_name, metadata)
    else:
        _send_event(session, event_name, metadata)
