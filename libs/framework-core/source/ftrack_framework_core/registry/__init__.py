# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from ftrack_utils.framework.dependencies import registry

logger = logging.getLogger(__name__)


class Registry(object):
    @property
    def schemas(self):
        '''
        Returns the registered schemas`
        '''
        return self.__registered_modules.get('schema')

    @property
    def tool_configs(self):
        '''
        Returns the registered tool_configs`
        '''
        return self.__registered_modules.get('tool_config')

    @property
    def plugins(self):
        '''
        Returns the registered plugins`
        '''
        return self.__registered_modules.get('plugin')

    @property
    def engines(self):
        '''
        Returns the registered engines`
        '''
        return self.__registered_modules.get('engine')

    @property
    def widgets(self):
        '''
        Returns the registered engines`
        '''
        return self.__registered_modules.get('widget')

    @property
    def registered_modules(self):
        return self.__registered_modules

    # TODO: we can create an engine registry

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
        self.__registered_modules = {}

        self.__tool_configs_registry = {}
        self.__schemas_registry = {}
        self.__plugins_registry = []
        self.__engines_registry = {}
        self.__widgets_registry = {}

    # Register
    def scan_modules(self, package_types, package_names):
        '''
        Scan site packages for the given *package_names* if the package name
        is found and contains the register.py file and is of type of the given
        *package_types*. The modules in the package gets registered.
        '''
        self.__registered_modules = registry.scan_modules(
            package_types, package_names
        )
