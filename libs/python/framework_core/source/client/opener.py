# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import client
from ftrack_connect_pipeline import constants


class OpenerClient(client.Client):
    '''
    Opener Client Base Class
    '''

    definition_filters = [constants.OPENER]

    def __init__(self, event_manager):
        '''
        Initialise OpenerClient with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(OpenerClient, self).__init__(event_manager)
