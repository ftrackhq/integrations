# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import client
from ftrack_connect_pipeline.constants import asset as asset_const


class LogViewerClient(client.Client):
    '''
    Log Viewer Client Base Class
    '''

    def __init__(self, event_manager):
        '''
        Initialise LogViewerClient with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(LogViewerClient, self).__init__(event_manager)
