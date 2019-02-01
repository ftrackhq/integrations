# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import functools
import logging
import ftrack_api
import threading
import maya.cmds as mc

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.configure_logging import configure_logging

configure_logging(__name__)
logger = logging.getLogger(__name__)


def run_local_events(session, event):
    logger.info('run_local_events:{}'.format(event))
    event_list = event['data']['event_list']
    results = []
    event_type = None
    for one_event in event_list:
        event_type = one_event['type']
        event_topic = one_event['topic']
        event_options = {'options': one_event.get('options',{})}
        event_data = {'data': one_event.get('data', [])}
        event_data.update(event_options)

        event = ftrack_api.event.base.Event(
            topic=str(event_topic),
            data=event_data
        )

        result = session.event_hub.publish(
            event,
            synchronous=True
        )
        if result:
            results.append(result[0])

    logger.info('Event result: {}'.format(results))
    return {event_type: results}


def start_host_listener():
    logger.info('START EVENT LISTENER')
    session = ftrack_api.Session(auto_connect_event_hub=False)
    session.event_hub.connect()
    session.event_hub.subscribe(
        'topic={}'.format(constants.PIPELINE_RUN_TOPIC),
        functools.partial(run_local_events, session)
    )
    session.event_hub.wait()


def register_hub_host():
    t = threading.Thread(target=start_host_listener)
    t.daemon = True
    t.start()
    logger.info('thread started!')




mc.evalDeferred("register_hub_host()")
