# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging

from ftrack_utils.extensions.registry import register_yaml_files
from ftrack_utils.paths import find_files

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

        for yaml_config_file_path in find_files(
            framework_extension_path,
            file_filter=lambda filename: filename
            == '{}.yaml'.format(dcc_name),
        ):
            for extension in register_yaml_files([yaml_config_file_path]):
                # Should only be one
                return extension

    raise ValueError(
        'Could not find DCC configuration file for "{0}" at extension paths {1}'.format(
            dcc_name, framework_extension_paths
        )
    )
