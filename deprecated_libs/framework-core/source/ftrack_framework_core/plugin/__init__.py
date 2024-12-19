# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from abc import ABC, abstractmethod


class BasePlugin(ABC):
    '''Base Class to represent a Plugin'''

    name = None

    def __repr__(self):
        return '<{}>'.format(self.name)

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._session

    @property
    def context_id(self):
        '''
        Returns the context_id where the plugin it's been executed on
        '''
        return self._context_id

    @property
    def options(self):
        '''Return the context options of the plugin'''
        return self._options

    def __init__(self, options, session, context_id=None):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._options = options
        self._session = session
        self._context_id = context_id

    def ui_hook(self, payload):
        '''
        Method to interact with the UI.
        *payload* Data provided from the ui.
        '''
        raise NotImplementedError('Missing ui_hook method.')

    @abstractmethod
    def run(self, store):
        '''
        Implementation of the plugin. *store* contains any previous published
        data from the executed tool-config
        '''
        raise NotImplementedError('Missing run method.')

    @classmethod
    def register(cls):
        '''
        Register function for the plugin to be discovered.
        '''
        import inspect

        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )
        logger.debug('registering: {}'.format(cls.name))

        data = {
            'extension_type': 'plugin',
            'name': cls.name,
            'extension': cls,
            'path': inspect.getfile(cls),
        }
        return data
