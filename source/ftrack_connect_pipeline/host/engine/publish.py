# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import BaseEngine


class PublisherEngine(BaseEngine):

    def __init__(self, event_manager, host,  hostid, asset_type,
                 extra_hosts_definitions=None):
        '''Initialise publisherEngine with *event_manager*, *host*, *hostid* and
        *asset_type*, *extra_hosts_definitions* is optional'''
        super(PublisherEngine, self).__init__(event_manager, host, hostid,
                                              asset_type,
                                              extra_hosts_definitions)



