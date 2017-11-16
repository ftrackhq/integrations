import hiero

import logging
from ftrack_shot_processor import FtrackShotProcessor, FtrackShotProcessorPreset
from ftrack_shot_processor_ui import FtrackShotProcessorUI

from hiero.exporters import FnNukeAnnotationsExporter
from hiero.exporters import FnExternalRender
from hiero.exporters import FnNukeShotExporter


registry = hiero.core.taskRegistry
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_processors():

    # Register the ftrack shot processor.
    hiero.ui.taskUIRegistry.registerProcessorUI(
        FtrackShotProcessorPreset, FtrackShotProcessorUI
    )

    hiero.core.taskRegistry.registerProcessor(
        FtrackShotProcessorPreset, FtrackShotProcessor
    )

    # Register the base preset for ftrack shot processor.
    # this could be moved to a discover function
    name = 'Base Preset'

    nuke_script_processor = FnNukeAnnotationsExporter.NukeAnnotationsPreset(
        "nuke script",
        {
            'readPaths': [],
            'writePaths': [""],
            'timelineWriteNode': ""
        }

    )

    external_render = FnExternalRender.NukeRenderPreset(
        "plate",
        {
            "file_type": "dpx",
            "dpx": {"datatype": "10 bit"}
        }
    )

    properties = {
        "exportTemplate": (
            (
                '{ftrack}.{ext}',
                nuke_script_processor
            ),
            (
                '{ftrack}.{ext}',
                external_render
            )
        )
    }

    preset = FtrackShotProcessorPreset(
        name,
        properties
    )

    existing = [p.name() for p in registry.localPresets()]
    if name in existing:
        registry.removeProcessorPreset(name)

    hiero.core.taskRegistry.removeProcessorPreset(name)
    hiero.core.taskRegistry.addProcessorPreset(name, preset)
