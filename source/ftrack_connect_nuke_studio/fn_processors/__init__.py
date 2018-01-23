import os
import hiero

import logging
from ftrack_shot_processor import FtrackShotProcessor
from ftrack_shot_processor_preset import FtrackShotProcessorPreset
from ftrack_shot_processor_ui import FtrackShotProcessorUI

from hiero.exporters import FnTranscodeExporter
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

    nuke_script_processor = FnNukeShotExporter.NukeShotPreset(
        "NukeScript",
        {
            'readPaths': [],
            'writePaths': [ftrack_server_path],
            'timelineWriteNode': "",
            'ftrack': {
                'asset_type_code':'script',
                'component_pattern': '{shot}.{ext}'
            }
        }
    )

    external_render = FnTranscodeExporter.TranscodePreset(
        "Plate",
        {
            "file_type": "dpx",
            "dpx": {"datatype": "10 bit"},
            'ftrack': {
                'asset_type_code':'img',
                'component_pattern': '{shot}.####.{ext}'
            }
        }
    )

    properties = {
        "exportTemplate": (
            (
                ftrack_server_path,
                nuke_script_processor
            ),
            (
                ftrack_server_path,
                external_render
            ),
        ),
        "cutLength" : True,
        "ftrack":{
            'project_schema': 'Film Pipeline',
            'task_type':  'Render',
            'task_status': 'Not Started',
            'shot_status': 'In progress',
            'asset_version_status': 'WIP'
        }
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
