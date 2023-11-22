# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import sys

from ftrack_utils.extensions.registry import register_yaml_files


def read_dcc_config(dcc_name, module_path):
    '''Locate and read the DCC config file based on *module_path*. As DCC:s
    only can be launcher from Connect, assume module path being within a Connect
    plugin dependencies folder'''

    connect_plugin_path = os.path.abspath(
        os.path.join(module_path, '..', '..')
    )

    config_path = connect_plugin_path

    if not os.path.isdir(config_path):
        raise ValueError(
            'Could not find DCC configuration file base {0}'.format(
                config_path
            )
        )

    files = os.listdir(config_path)

    yaml_config_file_paths = [
        os.path.join(config_path, str(config))
        for config in files
        if config == '{}.yaml'.format(dcc_name)
    ]

    for extension in register_yaml_files(yaml_config_file_paths):
        # Should only be one
        result = extension
        if 'framework_extension_paths' in result:
            # Expand paths, support:
            #   - paths being based on environment variables
            #   - relative paths
            #   - absolute paths
            framework_extension_paths_expanded = []
            for path in result['framework_extension_paths']:
                if not len(path or ""):
                    continue
                if path.startswith('$'):
                    # Assume environment variable
                    path = os.environ.get(
                        path[path.find("{") + 1, path.rfind("}")], path
                    )
                elif path[1] != os.sep and not (
                    sys.platform == 'win32'
                    and len(path) >= 2
                    and path[1] == ':'
                ):
                    # Relative path, append config path
                    path = os.path.join(config_path, path)
                else:
                    # Absolute path, keep as is
                    pass
                if not os.path.exists(path):
                    raise ValueError(
                        'Framework extension path {0} is invalid!'.format(path)
                    )
                framework_extension_paths_expanded.append(path)
            result[
                'framework_extension_paths'
            ] = framework_extension_paths_expanded
        return result

    raise ValueError(
        'Could not DCC find configuration file for "{0}" at {1}'.format(
            dcc_name, config_path
        )
    )
