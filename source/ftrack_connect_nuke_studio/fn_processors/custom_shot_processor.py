# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import hiero.ui
from hiero.exporters import FnShotProcessor
import logging

from hiero.exporters import FnNukeAnnotationsExporterUI, FnNukeAnnotationsExporter
from hiero.exporters import FnTranscodeExporterUI, FnTranscodeExporter

logger = logging.getLogger(
    __name__
)


class FtrackShotProcessor(hiero.core.ProcessorBase):

    def __init__(self, preset, submission, synchronous=False):
        super(FtrackShotProcessor, self).__init__(
            preset, submission, synchronous=synchronous
        )

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def startProcessing(self, exportItems, preview=False):
        self.logger.info('============= start processing! ===========')
        taskGroup = hiero.core.TaskGroup()
        for trackitem in exportItems:
            self.logger.info('Processing item: %s ' % trackitem)

            taskGroup.setTaskDescription(trackitem.name())
            for name, proc_ui, proc_preset, proc_exec in self._preset.properties()['processors']:
                self.logger.info('Processing : %s' % proc_exec())

    def setPreset(self, preset):
        self._preset = preset
        self._exportTemplate = hiero.core.ExportStructure2()

    def preset(self):
        return self._preset


class FtrackProcessorPreset(hiero.core.ProcessorPreset):

    def __init__(self, name, properties, task=FtrackShotProcessor):

        super(FtrackProcessorPreset, self).__init__(
            task, name
        )

        self.properties().update(properties)
        self.properties()['exportRoot'] = '/usr/tmp'
        self.properties()['exportTemplate'] = ''

        '''
        NOTE: could these be just the names ? eg:

        {
        'plate',
        ''

        }
        '''

        self.properties()['processors'] = [
            (
                'plate',
                FnTranscodeExporter.TranscodePreset,
            ),
            (
                'nukescript',
                FnNukeAnnotationsExporter.NukeAnnotationsPreset,
            )
        ]

    def supportedItems(self):
        return hiero.core.TaskPresetBase.kAllItems
