import hiero

import logging
from custom_shot_processor import FtrackShotProcessor, FtrackProcessorPreset
from custom_shot_processor_ui import FtrackShotProcessorUI
from hiero.exporters import FnTranscodeExporter


registry = hiero.core.taskRegistry
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_processors():
    name = 'Base Preset'

    hiero.ui.taskUIRegistry.registerProcessorUI(
        FtrackProcessorPreset, FtrackShotProcessorUI
    )

    hiero.core.taskRegistry.registerProcessor(
        FtrackProcessorPreset, FtrackShotProcessor
    )

    preset = FtrackProcessorPreset(
        name,
        {
            "processors": [
                (
                    'plate', FnTranscodeExporter.TranscodePreset(
                        '', {'file_type': 'dpx', 'dpx': {'datatype': '10 bit'}}
                    )
                )
            ]
        }
    )
    logger.info('registering %s with %s ' % (name, preset))

    existing = [p.name() for p in registry.localPresets()]
    if name in existing:
        registry.removeProcessorPreset(name)

    hiero.core.taskRegistry.removeProcessorPreset(name)
    hiero.core.taskRegistry.addProcessorPreset(name, preset)
