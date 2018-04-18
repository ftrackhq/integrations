import hiero

import logging
from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_shot_processor import FtrackShotProcessor, FtrackShotProcessorPreset, FtrackShotProcessorUI
from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_timeline_processor import FtrackTimelineProcessorPreset

# custom processors
from ftrack_connect_nuke_studio.processors.ftrack_processors.ftrack_nuke_shot_exporter import FtrackNukeShotExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_processors.ftrack_nuke_render_exporter import FtrackNukeRenderExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_processors.ftrack_audio_exporter import FtrackAudioExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_processors.ftrack_edl_exporter import FtrackEDLExporterPreset
from ftrack_base import FTRACK_SHOT_PATH, FTRACK_SHOW_PATH

registry = hiero.core.taskRegistry
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# override foundry logger to get some useful output
hiero.core.log = logger


def register_processors():

    ftrack_shot_path = FTRACK_SHOT_PATH
    ftrack_show_path = FTRACK_SHOW_PATH

    # Register the base preset for ftrack shot processor.
    # this could be moved to a discover function
    shot_name = 'Ftrack Shot Preset'

    nuke_script_processor = FtrackNukeShotExporterPreset(
        'NukeScript',
        {
            'readPaths': [],
            'writePaths': [ftrack_shot_path],
            'timelineWriteNode': '',
        }
    )

    nuke_render_processor = FtrackNukeRenderExporterPreset(
        'Plate',
        {
            'file_type': 'dpx',
            'dpx': {
                'datatype': '10 bit'
            }
        }
    )

    audio_processor = FtrackAudioExporterPreset(
        'Audio', {}
    )

    shot_properties = {
        'exportTemplate': (
            (ftrack_shot_path, nuke_script_processor),
            (ftrack_shot_path, nuke_render_processor),
            # (ftrack_shot_path, audio_processor),

        ),
        'cutLength': True,
    }

    shot_preset = FtrackShotProcessorPreset(
        shot_name,
        shot_properties
    )

    # Register the base preset for ftrack timeline processor.
    # this could be moved to a discover function
    timeline_name = 'Ftrack Timeline Preset'

    edl_processor = FtrackEDLExporterPreset(
        'EDL', {}
    )

    timeline_properties = {
        'exportTemplate': (
            (ftrack_show_path, edl_processor),
        ),
        'cutLength': True,
    }

    timeline_preset = FtrackTimelineProcessorPreset(
        timeline_name,
        timeline_properties

    )

    registers = [
        (shot_name, shot_preset),
        (timeline_name, timeline_preset),

    ]

    for register_name, register_preset in registers:
        existing = [p.name() for p in registry.localPresets()]
        if shot_name in existing:
            registry.removeProcessorPreset(register_name)
        logger.debug('Registering Ftrack Processor: {0}'.format(register_name))
        hiero.core.taskRegistry.removeProcessorPreset(register_name)
        hiero.core.taskRegistry.addProcessorPreset(register_name, register_preset)
