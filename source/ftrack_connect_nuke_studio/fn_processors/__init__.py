import hiero

from custom_shot_processor import FtrackShotProcessor, FtrackProcessorPreset
from custom_shot_processor_ui import FtrackShotProcessorUI


registry = hiero.core.taskRegistry


def register_processors():
    name = 'Base Preset'

    hiero.ui.taskUIRegistry.registerProcessorUI(
        FtrackProcessorPreset, FtrackShotProcessorUI
    )

    hiero.core.taskRegistry.registerProcessor(
        FtrackProcessorPreset, FtrackShotProcessor
    )

    shottemplate = (
        ("{shot}", None)
    )

    preset = FtrackProcessorPreset(
        name,
        {
            "exportTemplate": shottemplate,
            "cutLength": True
        }
    )

    existing = [p.name() for p in registry.localPresets()]
    if name in existing:
        registry.removeProcessorPreset(name)

    hiero.core.taskRegistry.removeProcessorPreset(name)
    hiero.core.taskRegistry.addProcessorPreset(name, preset)
