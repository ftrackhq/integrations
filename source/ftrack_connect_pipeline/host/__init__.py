# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import functools
from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.schema import SchemaManager
from ftrack_connect_pipeline.host.runner import PublisherRunner
from ftrack_connect_pipeline import event
import logging

logger = logging.getLogger(__name__)


def initialise(session, host):
    '''Initialize host with *session*, *host* and *ui*, return *hostid*'''

    #Starting new event thread
    event_thread = event.EventHubThread()
    event_thread.start(session)

    definition_manager = DefintionManager(session, host)
