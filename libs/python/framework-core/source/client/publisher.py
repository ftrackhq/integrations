# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import client
from ftrack_connect_pipeline import constants


class PublisherClient(client.Client):
    '''
    Publisher Client Base Class
    '''

    definition_filters = [constants.PUBLISHER]

    def __init__(self, event_manager):
        '''
        Initialise PublisherClient with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(PublisherClient, self).__init__(event_manager)
