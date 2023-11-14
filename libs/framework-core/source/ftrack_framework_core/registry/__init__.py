# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import uuid

import logging
from collections import defaultdict

from ftrack_utils.extensions import registry

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
                registry.get_extensions_from_directory(path)
            )
        for extension in discovered_extensions:
            self.add(**extension)

    def add(self, extension_type, name, extension, path):
        '''
        Add the given *extension_type* with *name*, *extension* and *path to
        the registry
        '''
        if extension_type == 'tool_config':
            self._augment_tool_config(extension)
        # We use extension_type and not type to not interfere with python
        # build in type
        self.__registry[extension_type].append(
            {
                "name": name,
                "extension": extension,
                "path": path,
            }
        )

    def _get(self, extensions, name, extension, path):
        '''
        Check given *extensions* list to match given *name*, *extension* and *path* if
        neither provided, return all available extensions
        '''
        if not any([name, extension, path]):
            return extensions
        found_extensions = []
        for _extension in extensions:
            if name and _extension['name'] != name:
                continue
            if extension and _extension['extension'] != extension:
                continue
            if path and _extension['path'] != path:
                continue
            found_extensions.append(_extension)
        return found_extensions

    def get(self, name=None, extension=None, path=None, extension_type=None):
        '''
        Return given matching *name*, *extension*, *path* or *extension_type*.
        If nothing provided, return all available extensions.
        '''
        found_extensions = []
        if extension_type:
            extensions = self.registry.get(extension_type)
            found_extensions.extend(
                self._get(extensions, name, extension, path)
            )
        else:
            for extension_type in list(self.registry.keys()):
                extensions = self.registry.get(extension_type)
                found_extensions.extend(
                    self._get(extensions, name, extension, path)
                )

        return found_extensions

    def _augment_tool_config(self, tool_config):
        tool_config['reference'] = uuid.uuid4()
        self._recursive_create_reference(tool_config.get('engine'))
        return tool_config

    def _recursive_create_reference(self, tool_config_engine_portion):
        for item in tool_config_engine_portion:
            if isinstance(item, str):
                item['reference'] = uuid.uuid4()
            elif isinstance(item, dict):
                if item["type"] == "group":
                    item['reference'] = uuid.uuid4()
                    for plugin_item in item.get("plugins", []):
                        plugin_item['reference'] = uuid.uuid4()
                        if plugin_item['type'] == "group":
                            self._recursive_create_reference(plugin_item)
                elif item["type"] == "plugin":
                    item['reference'] = uuid.uuid4()
