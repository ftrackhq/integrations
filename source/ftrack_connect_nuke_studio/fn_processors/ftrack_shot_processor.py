# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

from hiero.exporters.FnShotProcessor import ShotProcessorPreset
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI

from .ftrack_base import FtrackBaseProcessor, FtrackBaseProcessorPreset, FtrackBaseProcessorUI


class FtrackShotProcessor(ShotProcessor, FtrackBaseProcessor):
    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBaseProcessor.__init__(self, preset, submission, synchronous=synchronous)

    def processTaskPreQueue(self):
        self.logger.debug('processing task pre queue')
        self.logger.debug(self._submission)
        ShotProcessor.processTaskPreQueue(self)


class FtrackShotProcessorUI(ShotProcessorUI, FtrackBaseProcessorUI):

    def __init__(self, preset):
        ShotProcessorUI.__init__(self, preset)
        FtrackBaseProcessorUI.__init__(self, preset)

    def displayName(self):
        return "Ftrack"

    def toolTip(self):
        return "Process as Shots generates output on a per shot basis."

    def updatePathPreview(self):
        self._pathPreviewWidget.setText('Ftrack Server: {0}'.format(self.session.server_url))


class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackBaseProcessorPreset):
    def __init__(self, name, properties):
        ShotProcessorPreset.__init__(self, name, properties)
        FtrackBaseProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackShotProcessor