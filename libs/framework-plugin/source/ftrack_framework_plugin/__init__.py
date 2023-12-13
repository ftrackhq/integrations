# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging
from abc import ABC, abstractmethod

import ftrack_constants.framework as constants


# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))


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
    def status(self):
        '''Current status of the plugin'''
        return self._status

    @status.setter
    def status(self, value):
        '''Set new status to the plugin'''
        if value not in constants.status.STATUS_LIST:
            self.logger.error(
                "Status {} is not recognized. Available statuses are: {}".format(
                    value, constants.status.STATUS_LIST
                )
            )
            value = constants.status.EXCEPTION_STATUS
        self._status = value

    @property
    def message(self):
        '''Current message'''
        return self._message

    @message.setter
    def message(self, value):
        '''Set the current message'''
        self._message = value

    @property
    def options(self):
        '''Return the context options of the plugin'''
        return self._options

    def __init__(self, options, session):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._options = options
        self._session = session
        self._status = constants.status.UNKNOWN_STATUS
        self._message = ''

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

        Return: Returning status and message is supported.
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
