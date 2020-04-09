# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.plugin import base

class LoaderCollectorPlugin(base.BaseCollectorPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''
    return_type = list
    plugin_type = constants.PLUGIN_LOADER_COLLECTOR_TYPE
    _required_output = []

    def __init__(self, session):
        '''Initialise CollectorPlugin with *session*

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''
        super(LoaderCollectorPlugin, self).__init__(session)