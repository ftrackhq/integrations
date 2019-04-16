# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import functools
from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import PublisherRunner
from ftrack_connect_pipeline import event, constants, utils
import logging

logger = logging.getLogger(__name__)



def provide_host_information(hostid, event):
    '''return the current hostid'''
    logger.info('providing hostid: {}'.format(hostid))
    context_id = utils.get_current_context()
    return {'hostid': hostid, 'context_id': context_id}


def initialise(session, host, ui):
    '''Initialize host with *session*, *host* and *ui*, return *hostid*'''
    hostid = '{}-{}-{}'.format(host, ui, uuid.uuid4().hex)

    event_thread = event.NewApiEventHubThread()
    event_thread.start(session)

    definition_manager = DefintionManager(session, host, hostid)
    package_results = definition_manager.packages.result()
    PublisherRunner(session, package_results, host, ui, hostid)

    is_remote_event = utils.remote_event_mode()

    if is_remote_event:
        logger.info('initialising host: {}'.format(hostid))

        handle_event = functools.partial(provide_host_information, hostid)
        session.event_hub.subscribe(
            'topic={}'.format(
                constants.PIPELINE_DISCOVER_HOST
            ),
            handle_event
        )

    return hostid



