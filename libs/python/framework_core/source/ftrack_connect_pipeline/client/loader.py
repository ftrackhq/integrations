# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import client
from ftrack_connect_pipeline import constants


class LoaderClient(client.Client):
    '''
    Loader Client Base Class
    '''

    definition_filters = [constants.LOADER]

    def __init__(self, event_manager, multithreading_enabled=True):
        '''
        Initialise OpenerClient with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(LoaderClient, self).__init__(
            event_manager, multithreading_enabled=multithreading_enabled
        )
