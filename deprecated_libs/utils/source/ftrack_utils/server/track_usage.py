# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

from ftrack_utils.decorators import asynchronous
from ftrack_utils.server.send_event import send_async_event, send_event


logger = logging.getLogger('ftrack_utils:usage')


def send_usage_event(session, event_name, metadata=None, _asynchronous=True):
    '''Send usage event with *event_name* and *metadata*.

    If asynchronous is True, the event will be sent in a new thread.
    '''

    if _asynchronous:
        send_async_event(session, '_track_usage', event_name, metadata)
    else:
        send_event(session, '_track_usage', event_name, metadata)
