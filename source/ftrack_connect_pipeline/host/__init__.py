# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import PublisherRunner
from ftrack_connect_pipeline import event, constants
import logging

logger = logging.getLogger(__name__)


def initalise(session, host, ui):
    '''Initialize host with *session*, *host* and *ui*, return *hostid*'''
    hostid = '{}-{}-{}'.format(host, ui, uuid.uuid4().hex)

    event_thread = event.NewApiEventHubThread()
    event_thread.start(session)

    definition_manager = DefintionManager(session, hostid)
    package_results = definition_manager.packages.result()
    PublisherRunner(session, package_results, host, ui, hostid)
    logger.info('initialising host: {}'.format(hostid))

    def provide_hostid(event):
        logger.info('providing hostid: {} from event: {}'.format(hostid, event))
        return hostid

    session.event_hub.subscribe(
        'topic={}'.format(
            constants.PIPELINE_DISCOVER_HOST
        ),
        provide_hostid
    )

    return hostid



