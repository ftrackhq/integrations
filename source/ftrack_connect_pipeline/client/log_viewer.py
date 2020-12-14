# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from ftrack_connect_pipeline import client
from ftrack_connect_pipeline.constants import asset as asset_const


class LogViewerClient(client.Client):
    '''
    Base client class.
    '''

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    def __init__(self, event_manager):
        '''Initialise AssetManagerClient with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''
        super(LogViewerClient, self).__init__(event_manager)
