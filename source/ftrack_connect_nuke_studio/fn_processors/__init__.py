import os
import hiero

import logging
from ftrack_shot_processor import FtrackShotProcessor, FtrackShotProcessorPreset, FtrackShotProcessorUI

# custom processors
from ftrack_nuke_shot_exporter import FtrackNukeShotExporterPreset
from ftrack_nuke_render_exporter import FtrackNukeRenderExporterPreset
from ftrack_audio_exporter import FtrackAudioExporterPreset
from ftrack_edl_exporter import FtrackEDLExporterPreset
from ftrack_base import FTRACK_SHOT_PATH, FTRACK_SHOW_PATH

registry = hiero.core.taskRegistry
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# override foundry logger to get some useful output
hiero.core.log = logger


def register_processors():

    # Register the ftrack shot processor.
    hiero.ui.taskUIRegistry.registerProcessorUI(
        FtrackShotProcessorPreset, FtrackShotProcessorUI
    )

    hiero.core.taskRegistry.registerProcessor(
        FtrackShotProcessorPreset, FtrackShotProcessor
    )

    ftrack_shot_path = FTRACK_SHOT_PATH
    ftrack_show_path = FTRACK_SHOW_PATH

    # Register the base preset for ftrack shot processor.
    # this could be moved to a discover function
    name = 'Base Preset'

    nuke_script_processor = FtrackNukeShotExporterPreset(
        "NukeScript",
        {
            'readPaths': [],
            'writePaths': [ftrack_shot_path],
            'timelineWriteNode': "",
        }
    )

    nuke_render_processor = FtrackNukeRenderExporterPreset(
        "Plate",
        {
            'file_type': 'dpx',
            'dpx': {
                'datatype': '10 bit'
            }
        }
    )

    audio_processor = FtrackAudioExporterPreset(
        "Audio", {}
    )

    edl_processor = FtrackEDLExporterPreset(
        "EDL", {}
    )

    properties = {
        "exportTemplate": (
            (ftrack_shot_path, nuke_script_processor),
            (ftrack_shot_path, nuke_render_processor),
            (ftrack_shot_path, audio_processor),
            (ftrack_show_path, edl_processor)
        ),
        "cutLength": True,
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
