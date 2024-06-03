# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os.path
import uuid
import pkgutil
import inspect

import logging
from collections import defaultdict

from ftrack_utils.extensions import registry, overrides

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
    def launch_configs(self):
        '''
        Returns the registered launcher configs`
        '''
        return self.__registry.get('launch_config')

    @property
    def dcc_configs(self):
        '''
        Returns the registered dcc configs`
        '''
        return self.__registry.get('dcc_config')

    @property
    def functions_js(self):
        '''
        Returns the registered Javascript functions`
        '''
        return self.__registry.get('functions_js')

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
    def scan_extensions(self, paths, extension_types=None):
        '''
        Scan framework extension modules from the given *paths*. If *extension_types*
        is given, only consider the given extension types.
        '''
        unique_extensions = []

        discovered_extensions = []
        for path in reversed(paths):
            logging.debug(
                f'Scanning {path} for {f"{extension_types} " if extension_types else ""}extensions'
            )
            dir_extensions = registry.get_extensions_from_directory(
                path, extension_types=extension_types
            )
            # Merge/override
            unique_extensions = overrides.set_overrides(
                discovered_extensions, dir_extensions
            )

        for extension in unique_extensions:
            self.add(**extension)

    def add(self, extension_type, name, extension, path):
        '''
        Add the given *extension_type* with *name*, *extension* and *path to
        the registry
        '''
        if extension_type == 'tool_config':
            self.augment_tool_config(extension)
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

    def get_one(self, *args, **kwargs):
        '''
        Return the extension mathing the given arguments, if not found or
        multiple found raise exception.
        '''
        matching_extensions = self.get(*args, **kwargs)
        if len(matching_extensions) == 0:
            kwargs_string = ''.join([('%s=%s' % x) for x in kwargs.items()])
            raise Exception(
                "Extension not found. Arguments: {}".format(
                    (''.join(args), kwargs_string)
                )
            )

        if len(matching_extensions) > 1:
            kwargs_string = ''.join([('%s=%s' % x) for x in kwargs.items()])
            raise Exception(
                "Multiple matching extensions found.Arguments: {}".format(
                    (''.join(args), kwargs_string)
                )
            )
        return matching_extensions[0]

    def augment_tool_config(self, tool_config):
        '''
        Augment the given *tool_config* to add a reference id to it
        and each plugin and group
        '''
        tool_config['reference'] = uuid.uuid4().hex
        if 'engine' in tool_config:
            self._recursive_create_reference(tool_config['engine'])
        return tool_config

    def _recursive_create_reference(self, tool_config_engine_portion):
        '''
        Recursive method to add reference number to each plugin and group of the
        given engine portion of a tool_config.
        '''
        for item in tool_config_engine_portion:
            if isinstance(item, str):
                # Convert string plugin to dictionary
                index = tool_config_engine_portion.index(item)
                tool_config_engine_portion[index] = {
                    'type': 'plugin',
                    'plugin': item,
                    'reference': f'{item}-{uuid.uuid4().hex}',
                }
                continue
            elif isinstance(item, dict):
                if item["type"] == "group":
                    item['reference'] = f'{item["type"]}-{uuid.uuid4().hex}'
                    for plugin_item in item.get("plugins", []):
                        if isinstance(plugin_item, str):
                            # Convert string plugin to dictionary
                            index = item['plugins'].index(plugin_item)
                            item['plugins'][index] = {
                                'type': 'plugin',
                                'plugin': plugin_item,
                                'reference': f'{plugin_item}-{uuid.uuid4().hex}',
                            }
                            continue
                        plugin_item[
                            'reference'
                        ] = f'{plugin_item["plugin"]}-{uuid.uuid4().hex}'
                        if plugin_item['type'] == "group":
                            self._recursive_create_reference(
                                plugin_item.get('plugins')
                            )
                elif item["type"] == "plugin":
                    item['reference'] = f'{item["plugin"]}-{uuid.uuid4().hex}'
