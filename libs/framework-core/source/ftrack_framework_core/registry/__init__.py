# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
from collections import defaultdict

from ftrack_utils.framework.dependencies import registry

logger = logging.getLogger(__name__)


class Registry(object):
    @property
    def schemas(self):
        '''
        Returns the registered schemas`
        '''
        return self.__registry.get('schema')

    @property
    def tool_configs(self):
        '''
        Returns the registered tool_configs`
        '''
        return self.__registry.get('tool_config')

    @property
    def plugins(self):
        '''
        Returns the registered plugins`
        '''
        return self.__registry.get('plugin')

    @property
    def engines(self):
        '''
        Returns the registered engines`
        '''
        return self.__registry.get('engine')

    @property
    def widgets(self):
        '''
        Returns the registered engines`
        '''
        return self.__registry.get('widget')

    @property
    def dialogs(self):
        '''
        Returns the registered engines`
        '''
        return self.__registry.get('dialog')

    @property
    def registered_modules(self):
        return self.__registry

    @property
    def registry(self):
        return self.__registry

    def __init__(self):
        '''
        Initialise Registry
        '''
        super(Registry, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.logger.debug('Initializing Registry {}'.format(self))

        # Reset all registries
        self.__registry = defaultdict(list)

    # Register
    def scan_extensions(self, paths):
        '''
        Scan framework extension modules from the given *paths*
        '''

        discovered_extensions = []
        for path in paths:
            discovered_extensions.extend(
                registry.get_framework_extensions_from_directory(path)
            )
        for extension in discovered_extensions:
            self.add(**extension)

    def add(self, extension_type, name, cls):
        # We use extension_type and not type to not interfere with python
        # build in type
        self.__registry[extension_type].append(
            {
                # TODO: name will be renamed to id in further tasks
                "name": name,
                "cls": cls,
            }
        )
