# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core import client
from framework_core import constants


class PublisherClient(client.Client):
    '''
    Publisher Client Base Class
    '''

    definition_filters = [constants.PUBLISHER]

    def __init__(self, event_manager):
        '''
        Initialise PublisherClient with instance of
        :class:`~framework_core.event.EventManager`
        '''
        super(PublisherClient, self).__init__(event_manager)
