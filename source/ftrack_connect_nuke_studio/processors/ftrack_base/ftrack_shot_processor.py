# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import hiero

from hiero.exporters.FnShotProcessor import ShotProcessorPreset
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI

from QtExt import QtWidgets

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import FtrackProcessorPreset, FtrackProcessor, FtrackProcessorUI


class FtrackShotProcessor(ShotProcessor, FtrackProcessor):
    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackProcessor.__init__(self, preset)


class FtrackShotProcessorUI(ShotProcessorUI, FtrackProcessorUI):

    def __init__(self, preset):
        ShotProcessorUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

    def displayName(self):
        return 'Ftrack Shot Processor'

    def toolTip(self):
        return 'Process as Shots generates output on a per shot basis.'

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


class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackProcessorPreset):
    def __init__(self, name, properties):
        ShotProcessorPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackShotProcessor

    def addCustomResolveEntries(self, resolver):
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)


# Register the ftrack shot processor.
hiero.ui.taskUIRegistry.registerProcessorUI(
    FtrackShotProcessorPreset, FtrackShotProcessorUI
)

hiero.core.taskRegistry.registerProcessor(
    FtrackShotProcessorPreset, FtrackShotProcessor
)
