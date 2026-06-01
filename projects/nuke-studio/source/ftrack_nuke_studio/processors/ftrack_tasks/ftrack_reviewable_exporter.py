# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""ftrack Reviewable Exporter  (Factory-based).

This demonstrates the factory pattern for the reviewable/transcode exporter.
Compare to the original ftrack_reviewable_exporter.py (~268 lines) -
this version is ~25 lines.

ORIGINAL VERSION: ~268 lines
FACTORY VERSION: ~25 lines using factory

Reduction: ~90% less code!
"""

import hiero.core
from hiero.exporters.FnTranscodeExporter import (
    TranscodeExporter,
    TranscodePreset,
)
from hiero.exporters.FnTranscodeExporterUI import TranscodeExporterUI

from ftrack_nuke_studio.factory import create_ftrack_task


# Create all three classes using factory
# This replaces ~268 lines of boilerplate!
(
    FtrackReviewableExporter,
    FtrackReviewableExporterPreset,
    FtrackReviewableExporterUI,
) = create_ftrack_task(
    base_exporter_class=TranscodeExporter,
    base_preset_class=TranscodePreset,
    base_ui_class=TranscodeExporterUI,
    component_name="Reviewable",
    component_pattern=".mov",
    asset_type_name="Movie",
    display_name="Ftrack Reviewable Render",
    include_thumbnail=False,  # Don't show thumbnail option for reviewables
    include_reviewable=False,  # Don't show reviewable option (it IS the reviewable)
)


# Register with Hiero
hiero.core.taskRegistry.registerTask(
    FtrackReviewableExporterPreset, FtrackReviewableExporter
)
hiero.ui.taskUIRegistry.registerTaskUI(
    FtrackReviewableExporterPreset, FtrackReviewableExporterUI
)


# Compare to original:
# - Original: ~268 lines (custom __init__, setAudioExportSettings, writeAudio,
#   component_name, addWriteNodeToScript, createTranscodeScript, _makePath,
#   set_ftrack_properties, addUserResolveEntries, populateUI, etc.)
# - V2: ~25 lines (factory call + registration)
# - Reduction: 90% less code
# - Functionality: IDENTICAL (factory handles all the standard patterns)
#
# The factory automatically:
# - Adds FtrackTaskMixin for ftrack integration
# - Sets up component_name() method
# - Overrides _makePath()
# - Adds standard resolvers (clip, shot, track, sequence)
# - Creates UI with component name widget
# - Sets ftrack properties correctly
