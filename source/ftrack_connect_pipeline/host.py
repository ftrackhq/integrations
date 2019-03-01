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
        event_type = one_event['pipeline']['plugin_type']

        logger.info('one event: {}'.format(one_event))

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data=one_event
        )
        result = session.event_hub.publish(
            event,
            synchronous=True
        )

        if result:
            results.append(result[0])

    local_event_result = {event_type: results}
    logger.info('one event result: {}'.format(local_event_result))
    return local_event_result


def start_host_listener(host=None, ui=None):
    logger.info('start event listener')
    session = get_shared_session()
    session.event_hub.subscribe(
        'topic={}'.format(constants.PIPELINE_RUN_TOPIC),
        functools.partial(run_local_events, session, host=host, ui=ui)
    )
    session.event_hub.wait()
