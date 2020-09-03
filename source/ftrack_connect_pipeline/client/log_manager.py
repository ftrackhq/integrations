# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import client
from ftrack_connect_pipeline.constants import asset as asset_const


class LogManagerClient(client.Client):
    '''
    Base client class.
    '''

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def log_list(self):
        '''Return the current list of asset_info'''
        if self.host_connection:
            return self.host_connection.logs

    def __init__(self, event_manager):
        '''Initialise AssetManagerClient with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.
        '''
        super(LogManagerClient, self).__init__(event_manager)
    #     self._reset_log_list()
    #
    # def _reset_log_list(self):
    #     '''Empty the _ftrack_asset_list'''
    #     self._log_list = []

