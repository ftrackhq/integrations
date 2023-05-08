# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import client
from framework_core import constants


class LoaderClient(client.Client):
    '''
    Loader Client Base Class
    '''

    definition_filters = [constants.LOADER]

    def __init__(self, event_manager, multithreading_enabled=True):
        '''
        Initialise OpenerClient with instance of
        :class:`~framework_core.event.EventManager`
        '''
        super(LoaderClient, self).__init__(
            event_manager, multithreading_enabled=multithreading_enabled
        )
