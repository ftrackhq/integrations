# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import PublisherRunner
import logging

logger = logging.getLogger(__name__)


def initialise(event_manager, host):
    '''Initialize host with *session*, *host* and *ui*, return *hostid*'''
    DefintionManager(event_manager, host)
