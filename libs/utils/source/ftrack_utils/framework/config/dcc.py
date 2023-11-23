# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging

from ftrack_utils.extensions.registry import register_yaml_files

logger = logging.getLogger(__name__)


def read_dcc_config(dcc_name, framework_extension_paths):
    '''Locate and read the DCC config file based on *framework_extension_paths*.'''

    for framework_extension_path in framework_extension_paths:
        if not os.path.isdir(framework_extension_path):
            logger.warning(
                'Could not find framework extension directory: {0}'.format(
                    framework_extension_path
                )
            )
            continue

        for root, dirs, files in os.walk(framework_extension_path):
            yaml_config_file_paths = [
                os.path.join(root, str(config))
                for config in files
                if config == '{}.yaml'.format(dcc_name)
            ]

            if len(yaml_config_file_paths) == 0:
                continue

            for extension in register_yaml_files(yaml_config_file_paths):
                # Should only be one
                return extension

    raise ValueError(
        'Could not DCC find configuration file for "{0}" at extension paths {1}'.format(
            dcc_name, framework_extension_paths
        )
    )
