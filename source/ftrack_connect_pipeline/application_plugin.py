# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import abc
import logging

import ftrack_api
import ftrack_api.event.base


class BaseApplicationPlugin(object):
    '''Application plugin.'''

    __metaclass__ = abc.ABCMeta

    def __init__(self, context_id):
        '''Initialise with application *context_id*.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._context_id = context_id

        self.api_session = ftrack_api.Session(
            auto_connect_event_hub=False
        )

        self.register_assets()

    @abc.abstractmethod
    def get_plugin_information(self):
        '''Return plugin information.'''

    def register_assets(self):
        '''Register assets.'''
        self.logger.info('Registering assets.')
        result = self.api_session.event_hub.publish(
            ftrack_api.event.base.Event(
                topic='ftrack.pipeline.register-assets',
                data=dict()
            ),
            synchronous=True
        )
        for item in result:
            self.logger.info('Registered asset: {0!r}'.format(item))

    def get_context(self):
        '''Return context.'''
        return self.api_session.get('Context', self._context_id)

    def set_context(self, context_id):
        '''Set context and emit event.'''
        old_context_id = self._context_id
        self._context_id = context_id
        event = ftrack_api.event.base.Event(
            topic='ftrack.context-changed',
            data={'context_id': context_id, 'old_context_id': old_context_id}
        )
        self.api_session.event_hub.publish(event, synchronous=True)
