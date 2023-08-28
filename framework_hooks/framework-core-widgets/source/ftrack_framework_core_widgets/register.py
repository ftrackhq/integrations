# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_widget.widget import BaseUI
from ftrack_utils.framework.dependencies import registry


def register(event_manager):
    current_dir = os.path.dirname(__file__)
    return registry.register_dependencies_from_directory(
        BaseUI, current_dir, event_manager
    )
