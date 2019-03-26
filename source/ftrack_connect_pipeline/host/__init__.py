# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import PublisherRunner
from ftrack_connect_pipeline import event, constants
import logging

logger = logging.getLogger(__name__)


def initalise(session, host, ui):
    hostid = '{}-{}-{}'.format(host, ui, uuid.uuid4().hex)

    event_thread = event.NewApiEventHubThread()
    event_thread.start(session)

    definition_manager = DefintionManager(session, hostid)
    PublisherRunner(session, definition_manager.packages, host, ui, hostid)
    logger.info('initialising host: {}'.format(hostid))
    return hostid



