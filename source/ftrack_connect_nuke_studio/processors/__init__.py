# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging

import hiero

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_shot_processor import (
    FtrackShotProcessor,
    FtrackShotProcessorPreset,
    FtrackShotProcessorUI
)
from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_timeline_processor import FtrackTimelineProcessorPreset
from ftrack_connect_nuke_studio.processors.ftrack_tasks.ftrack_copy_exporter import FtrackCopyExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_tasks.ftrack_nuke_shot_exporter import FtrackNukeShotExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_tasks.ftrack_nuke_render_exporter import FtrackNukeRenderExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_tasks.ftrack_audio_exporter import FtrackAudioExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_tasks.ftrack_edl_exporter import FtrackEDLExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_tasks.ftrack_otio_exporter import FtrackOTIOExporterPreset
from ftrack_connect_nuke_studio.processors.ftrack_tasks.ftrack_reviewable_exporter import FtrackReviewableExporterPreset

from .ftrack_base import FTRACK_PROJECT_STRUCTURE

registry = hiero.core.taskRegistry

logger = logging.getLogger(__name__)


def register_processors():

    # Register the base preset for ftrack shot processor.
    # this could be moved to a discover function
    shot_name = 'Ftrack Shot Preset'


    nuke_script_processor = FtrackNukeShotExporterPreset(
        '', {}
    )

    reviewable_processor = FtrackReviewableExporterPreset(
        '',
        {
            'file_type': 'mov',
            'mov': {
                'encoder': 'mov64',
                'codec': 'avc1\tH.264',
                'quality': 3,
                'settingsString': 'H.264, High Quality',
                'keyframerate': 1,
            }
        }
    )

    nuke_render_processor = FtrackNukeRenderExporterPreset(
        '',
        {
            'file_type': 'dpx',
            'dpx': {
                'datatype': '10 bit'
            }
        }
    )

    audio_processor = FtrackAudioExporterPreset(
        '', {}
    )

    copy_processor = FtrackCopyExporterPreset(
        '', {}
    )

    shot_properties = {
        'exportTemplate': (
            (FTRACK_PROJECT_STRUCTURE, nuke_render_processor),
            (FTRACK_PROJECT_STRUCTURE, nuke_script_processor),
            (FTRACK_PROJECT_STRUCTURE, reviewable_processor),
            (FTRACK_PROJECT_STRUCTURE, audio_processor),
            (FTRACK_PROJECT_STRUCTURE, copy_processor)

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

    edl_processor = FtrackOTIOExporterPreset(
        '', {}
    )

    timeline_properties = {
        'exportTemplate': (
            (FTRACK_PROJECT_STRUCTURE, edl_processor),
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
