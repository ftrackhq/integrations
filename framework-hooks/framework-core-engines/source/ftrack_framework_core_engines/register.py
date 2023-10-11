# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_engine import BaseEngine
from ftrack_utils.framework.dependencies import registry

PACKAGE_TYPE = "engine"


def register():
    current_dir = os.path.dirname(__file__)
    return registry.register_dependencies_from_directory(
        BaseEngine, current_dir
    )
