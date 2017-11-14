import hiero

import logging
from ftrack_shot_processor import FtrackShotProcessor, FtrackShotProcessorPreset
from ftrack_shot_processor_ui import FtrackShotProcessorUI
from hiero.exporters import FnNukeAnnotationsExporter


registry = hiero.core.taskRegistry
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_processors():
    name = 'Base Preset'

    hiero.ui.taskUIRegistry.registerProcessorUI(
        FtrackShotProcessorPreset, FtrackShotProcessorUI
    )

    hiero.core.taskRegistry.registerProcessor(
        FtrackShotProcessorPreset, FtrackShotProcessor
    )

    properties = {
        "processors": [
            (
                'nuke_script',
                FnNukeAnnotationsExporter.NukeAnnotationsPreset(
                    "",
                    {
                        'readPaths': [],
                        'writePaths': [""],
                        'timelineWriteNode': ""
                    }
                )
            )
        ]
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
