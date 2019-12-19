# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.runner import BaseRunner


class PublisherRunner(BaseRunner):

    def __init__(self, event_manager, host,  hostid):
        '''Initialise publish runnder with *session*, *package_definitions*, *host*, *ui* and *hostid*.'''
        super(PublisherRunner, self).__init__(event_manager, host,  hostid)



