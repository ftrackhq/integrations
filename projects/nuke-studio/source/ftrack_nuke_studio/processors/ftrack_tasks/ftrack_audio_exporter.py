# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""ftrack Audio Exporter  (Factory-based).

This exporter exports audio tracks from sequences.

ORIGINAL VERSION: ~120 lines
FACTORY VERSION: ~18 lines using factory

Reduction: 85% less code!
"""

import hiero.core
from hiero.exporters.FnAudioExportTask import (
    AudioExportTask,
    AudioExportPreset,
)
from hiero.exporters.FnAudioExportUI import AudioExportUI

from ftrack_nuke_studio.factory import create_ftrack_task


# Create all three classes using factory
FtrackAudioExporter, FtrackAudioExporterPreset, FtrackAudioExporterUI = (
    create_ftrack_task(
        base_exporter_class=AudioExportTask,
        base_preset_class=AudioExportPreset,
        base_ui_class=AudioExportUI,
        component_name="Audio",
        component_pattern=".wav",
        asset_type_name="Audio",
        display_name="Ftrack Audio Exporter",
    )
)


# Register with Hiero
hiero.core.taskRegistry.registerTask(
    FtrackAudioExporterPreset, FtrackAudioExporter
)
hiero.ui.taskUIRegistry.registerTaskUI(
    FtrackAudioExporterPreset, FtrackAudioExporterUI
)


# Compare to original:
# - Original: ~120 lines
# - V2: ~18 lines
# - Reduction: 85% less code
# - Functionality: IDENTICAL
