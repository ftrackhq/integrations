# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin
from ftrack_utils.framework.dependencies import registry

PACKAGE_TYPE = "plugin"


def register():
    current_dir = os.path.dirname(__file__)
    return registry.scan_modules_from_directory(BasePlugin, current_dir)
