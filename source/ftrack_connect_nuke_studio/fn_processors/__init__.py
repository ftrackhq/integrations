import os
import hiero

import logging
from ftrack_shot_processor import FtrackShotProcessor, FtrackShotProcessorPreset, FtrackShotProcessorUI

# custom processors
from ftrack_nuke_shot_exporter import FtrackNukeShotExporterPreset
from ftrack_nuke_render_exporter import FtrackNukeRenderExporterPreset
from ftrack_audio_exporter import FtrackAudioExporterPreset

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

    ftrack_server_path = os.path.join(
        '{ftrack_project}',
        '{ftrack_sequence}',
        '{ftrack_shot}',
        '{ftrack_task}',
        '{ftrack_asset}',
        '{ftrack_component}'
    )

    # Register the base preset for ftrack shot processor.
    # this could be moved to a discover function
    name = 'Base Preset'

    nuke_script_processor = FtrackNukeShotExporterPreset(
        "NukeScript",
        {
            'readPaths': [],
            'writePaths': [ftrack_server_path],
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

    # audio_processor = FtrackAudioExporterPreset(
    #     "Audio", {}
    # )

    properties = {
        "exportTemplate": (
            (ftrack_server_path, nuke_script_processor),
            (ftrack_server_path, nuke_render_processor),
            # (ftrack_server_path, audio_processor)
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
