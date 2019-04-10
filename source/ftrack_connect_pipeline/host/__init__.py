# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import functools
from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import PublisherRunner
from ftrack_connect_pipeline import event, constants
import logging

logger = logging.getLogger(__name__)


def provide_hostid(hostid, event):
    logger.info('providing hostid: {}'.format(hostid))
    return hostid


def initialise(session, host, ui):
    '''Initialize host with *session*, *host* and *ui*, return *hostid*'''
    hostid = '{}-{}-{}'.format(host, ui, uuid.uuid4().hex)

    event_thread = event.NewApiEventHubThread()
    event_thread.start(session)

    definition_manager = DefintionManager(session, host, hostid)
    package_results = definition_manager.packages.result()
    PublisherRunner(session, package_results, host, ui, hostid)
    logger.info('initialising host: {}'.format(hostid))

    handle_event = functools.partial(provide_hostid, hostid)
    session.event_hub.subscribe(
        'topic={}'.format(
            constants.PIPELINE_DISCOVER_HOST
        ),
        handle_event
    )

    return hostid



