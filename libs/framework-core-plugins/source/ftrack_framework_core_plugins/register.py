# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin.utils import register_plugins
import os


def register(event_manager, host_id, ftrack_object_manager):
    current_dir = os.path.dirname(__file__)
    return register_plugins.register(
        current_dir, event_manager, host_id, ftrack_object_manager
    )

