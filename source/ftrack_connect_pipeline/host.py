# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import functools
import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.session import get_shared_session

logger = logging.getLogger(__name__)


def run_local_events(session, event, host=None, ui=None):
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

        logger.info('event_data {}'.format(event_data))

        event = ftrack_api.event.base.Event(
            topic=str(event_topic),
            data={
                'pipeline': {
                    'type': 'plugin',
                    'ui': ui,
                    'host': host,
                },
                'settings': event_data
            }
        )

        result = session.event_hub.publish(
            event,
            synchronous=True
        )
        if result:
            results.append(result[0])

    logger.info('Event result: {}'.format(results))
    return {event_type: results}


def start_host_listener(host=None, ui=None):
    logger.info('start event listener')
    session = get_shared_session()
    session.event_hub.subscribe(
        'topic={}'.format(constants.PIPELINE_RUN_TOPIC),
        functools.partial(run_local_events, session, host=host, ui=ui)
    )
    session.event_hub.wait()
