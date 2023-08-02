# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin.utils import register_plugins


def register(event_manager, host_id, ftrack_object_manager):
    register_plugins.register(event_manager, host_id, ftrack_object_manager)

