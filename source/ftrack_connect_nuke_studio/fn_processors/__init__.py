import os
import hiero

import logging
from ftrack_shot_processor import FtrackShotProcessor, FtrackShotProcessorPreset, FtrackShotProcessorUI
from ftrack_sequence_processor import FtrackSequenceProcessor, FtrackSequenceProcessorPreset, FtrackSequenceProcessorUI

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

    # Register the ftrack sequence processor.
    hiero.ui.taskUIRegistry.registerProcessorUI(
        FtrackSequenceProcessorPreset, FtrackSequenceProcessorUI
    )

    hiero.core.taskRegistry.registerProcessor(
        FtrackSequenceProcessorPreset, FtrackSequenceProcessor
    )

    ftrack_shot_path = FTRACK_SHOT_PATH
    ftrack_show_path = FTRACK_SHOW_PATH

    # Register the base preset for ftrack shot processor.
    # this could be moved to a discover function
    shot_name = 'Shot Base Preset'

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


    shot_properties = {
        "exportTemplate": (
            (ftrack_shot_path, nuke_script_processor),
            (ftrack_shot_path, nuke_render_processor),
            (ftrack_shot_path, audio_processor),

        ),
        "cutLength": True,
    }

    shot_preset = FtrackShotProcessorPreset(
        shot_name,
        shot_properties
    )

    # Register the base preset for ftrack sequence processor.
    # this could be moved to a discover function
    sequence_name = 'Sequence Base Preset'

    edl_processor = FtrackEDLExporterPreset(
        "EDL", {}
    )

    sequence_properties = {
        "exportTemplate": (
            (ftrack_show_path, edl_processor),
        ),
        "cutLength": True,
    }

    sequence_preset = FtrackSequenceProcessorPreset(
        sequence_name,
        sequence_properties

    )


    existing = [p.name() for p in registry.localPresets()]
    if shot_name in existing:
        registry.removeProcessorPreset(shot_name)

    hiero.core.taskRegistry.removeProcessorPreset(shot_name)
    hiero.core.taskRegistry.addProcessorPreset(shot_name, shot_preset)

    if sequence_name in existing:
        registry.removeProcessorPreset(sequence_name)

    hiero.core.taskRegistry.removeProcessorPreset(sequence_name)
    hiero.core.taskRegistry.addProcessorPreset(sequence_name, sequence_preset)