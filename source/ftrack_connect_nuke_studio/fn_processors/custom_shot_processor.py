# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import hiero
from hiero.exporters import FnShotProcessor
import logging

from hiero.exporters import FnNukeAnnotationsExporterUI, FnNukeAnnotationsExporter
from hiero.exporters import FnTranscodeExporterUI, FnTranscodeExporter

logger = logging.getLogger(
    __name__
)


class FtrackShotProcessor(FnShotProcessor.ShotProcessor):

    def taskStep(self):
        print 'IN TASK STEP'
        self._finished = True
        return False


class FtrackProcessorPreset(FnShotProcessor.ShotProcessorPreset):
    def __init__(self, name, properties, task=FtrackShotProcessor):
        super(FtrackProcessorPreset, self).__init__(
            name=name, properties=properties
        )
        self.properties()['processors'] = [
            (
                'plate',
                FnTranscodeExporterUI.TranscodeExporterUI,
                FnTranscodeExporter.TranscodePreset
            ),
            ('nukescript',
                FnNukeAnnotationsExporterUI.NukeAnnotationsExporterUI,
                FnNukeAnnotationsExporter.NukeAnnotationsPreset
            )
        ]

    def supportedItems(self):
        return hiero.core.TaskPresetBase.kAllItems
