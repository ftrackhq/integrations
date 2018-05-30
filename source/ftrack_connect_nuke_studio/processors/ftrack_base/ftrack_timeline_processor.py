# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from hiero.exporters.FnTimelineProcessor import TimelineProcessor
from hiero.exporters.FnTimelineProcessor import TimelineProcessorPreset
from hiero.exporters.FnTimelineProcessorUI import TimelineProcessorUI

from QtExt import QtWidgets

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import FtrackProcessorPreset, FtrackProcessor, FtrackProcessorUI


class FtrackTimelineProcessor(TimelineProcessor, FtrackProcessor):
    def __init__(self, preset, submission, synchronous=False):
        TimelineProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackProcessor.__init__(self, preset)

    def startProcessing(self, exportItems, preview=False):

        self.create_project_structure(exportItems)
        result = FtrackProcessor.validateFtrackProcessing(self, exportItems)
        if result:
            TimelineProcessor.startProcessing(self, exportItems, preview)


class FtrackTimelineProcessorUI(TimelineProcessorUI, FtrackProcessorUI):

    def __init__(self, preset):
        TimelineProcessorUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

    def updatePathPreview(self):
        self._pathPreviewWidget.setText('Ftrack Server: {0}'.format(self.session.server_url))

    def _checkExistingVersions(self, exportItems):
        # disable version check as we handle this internally
        return True

    def createVersionWidget(self):
        # disable version widget
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def displayName(self):
        return 'Ftrack Timeline Processor'

    def toolTip(self):
        return 'Process as Shots generates output on a per shot basis.'

    def populateUI(self, processorUIWidget, taskUIWidget, exportItems):
        TimelineProcessorUI.populateUI(self, processorUIWidget, taskUIWidget, exportItems)
        FtrackProcessorUI.addFtrackProcessorUI(self, processorUIWidget, exportItems)


class FtrackTimelineProcessorPreset(TimelineProcessorPreset, FtrackProcessorPreset):
    def __init__(self, name, properties):
        TimelineProcessorPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackTimelineProcessor

    def addCustomResolveEntries(self, resolver):
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)


# Register the ftrack sequence processor.
hiero.ui.taskUIRegistry.registerProcessorUI(
    FtrackTimelineProcessorPreset, FtrackTimelineProcessorUI
)

hiero.core.taskRegistry.registerProcessor(
    FtrackTimelineProcessorPreset, FtrackTimelineProcessor
)