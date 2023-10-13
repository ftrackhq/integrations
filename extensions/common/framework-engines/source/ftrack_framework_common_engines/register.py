# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_engine import BaseEngine
from ftrack_utils.framework.dependencies import registry

EXTENSION_TYPE = "engine"


def register():
    current_dir = os.path.dirname(__file__)
    return registry.scan_modules_from_directory(BaseEngine, current_dir)
