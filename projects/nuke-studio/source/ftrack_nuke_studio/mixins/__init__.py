# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Mixins for adding ftrack functionality via composition."""

from ftrack_nuke_studio.mixins.ftrack_task_mixin import FtrackTaskMixin
from ftrack_nuke_studio.mixins.ftrack_preset_mixin import FtrackPresetMixin
from ftrack_nuke_studio.mixins.ftrack_ui_mixin import FtrackUIMixin

__all__ = [
    "FtrackTaskMixin",
    "FtrackPresetMixin",
    "FtrackUIMixin",
]
