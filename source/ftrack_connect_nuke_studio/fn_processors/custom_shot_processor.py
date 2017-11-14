# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.

import hiero
import hiero.core
from hiero.exporters import FnShotProcessor, FnNukeShotExporter
import logging

from hiero.exporters import FnNukeAnnotationsExporterUI, FnNukeAnnotationsExporter
from hiero.exporters import FnTranscodeExporterUI, FnTranscodeExporter

from .ftrack_base import FtrackBase

logger = logging.getLogger(
    __name__
)


class FtrackShotProcessor(hiero.core.ProcessorBase, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        super(FtrackShotProcessor, self).__init__(
            preset, submission, synchronous=synchronous
        )

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

    def startProcessing(self, exportItems, preview=False):
        self.logger.info('============= start processing! ===========')

        allTasks = []
        path = self._exportTemplate.exportRootPath()
        exportPath = ''
        trackItemVersion = 'v0'
        project = 'None'    
        cutHandles = None
        retime = None

        taskGroup = hiero.core.TaskGroup()
        for trackitem in exportItems:
            self.logger.info('Processing item: %s ' % trackitem)

            taskGroup.setTaskDescription(trackitem.name())
            for name, proc_preset in self._preset.properties()['processors']:
                pass

                # taskData = hiero.core.TaskData(
                #     proc_preset,
                #     trackitem,
                #     path,
                #     exportPath,
                #     trackItemVersion,
                #     self._exportTemplate,
                #     project=project,
                #     cutHandles=cutHandles,
                #     retime=retime,
                #     startFrame=startFrame,
                #     startFrameSource=proc_preset.properties()["startFrameSource"],
                #     resolver=resolver,
                #     submission=self._submission,
                #     skipOffline=self.skipOffline(),
                #     presetId=presetId,
                #     shotNameIndex = getShotNameIndex(trackitem)
                # )

                # task = hiero.core.taskRegistry.createTaskFromPreset(
                #     proc_preset, taskData
                # )
                # self.logger.info('executing task %s' % task)
                # taskGroup.addChild(task)
                # allTasks.append(task)
        self._submission.addChild(taskGroup)
        self._submission.setSynchronous()
        self.processTaskPreQueue()
        self._submission.addToQueue()

        return allTasks

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

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

        self.properties()['processors'] = []
        self.properties()['exportRoot'] = '/usr/tmp'
        self.properties()['exportTemplate'] = ''
        self.properties().update(properties)

    def supportedItems(self):
        return hiero.core.TaskPresetBase.kAllItems
