# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging

from abc import ABC, abstractmethod

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


class BaseEngine(ABC):
    '''
    Base engine class.
    '''

    name = None
    engine_types = ['base']
    '''Engine type for this engine class'''

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._session

    @property
    def plugin_registry(self):
        return self._plugin_registry

    def __init__(self, plugin_registry, session):
        '''
        Initialise BaseEngine with given *plugin_registry*.
        '''
        super(BaseEngine, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._plugin_registry = plugin_registry
        self._session = session

    @abstractmethod
    def run_plugin(self, plugin, store, options):
        '''
        Run given *plugin* accepting *store* and *options*.
        *plugin*: Name of the plugin to be executed.
        *store*: registry of plugin data.
        *options*: options to be passed to the plugin
        '''
        raise NotImplementedError

    @abstractmethod
    def execute_engine(self, engine):
        '''
        Execute given *engine* from a tool-config.
        *engine*: Portion list of a tool-config with groups and plugins.
        '''
        raise NotImplementedError

    @classmethod
    def register(cls):
        '''
        Register function for the engine to be discovered.
        '''
        import inspect

        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )

        logger.debug(
            'registering: {} for {}'.format(cls.name, cls.engine_types)
        )

        data = {
            'extension_type': 'engine',
            'name': cls.name,
            'extension': cls,
            'path': inspect.getfile(cls),
        }

        return data
