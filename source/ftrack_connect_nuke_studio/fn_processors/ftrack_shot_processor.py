# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile
import logging
import hiero
import hiero.core
from .ftrack_base import FtrackBase


class FtrackShotProcessor(hiero.core.ProcessorBase, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        FtrackBase.__init__(self)
        hiero.core.ProcessorBase.__init__(
            self, preset, submission, synchronous=synchronous
        )

    def startProcessing(self, exportItems, preview=False):
        self.logger.info('============= start processing! ===========')

        allTasks = []
        trackItemVersion = 'v0'

        taskGroup = hiero.core.TaskGroup()
        for trackitem in exportItems:
            self.logger.info('Processing item: %s ' % trackitem)

            taskGroup.setTaskDescription(trackitem.name())
            for name, proc_preset in self._preset.properties()['processors']:
                self.logger.info(
                    'executing: {0} with {1}'.format(name, proc_preset)
                )

                taskData = hiero.core.TaskData(
                    proc_preset,
                    trackitem,
                    exportRoot=tempfile.gettempdir(),
                    shotPath='',
                    version=trackItemVersion,
                    exportTemplate='',
                    project=None,
                )

                task = hiero.core.taskRegistry.createTaskFromPreset(
                    proc_preset, taskData
                )
                self.logger.info('executing task %s' % task)
                taskGroup.addChild(task)
                allTasks.append(task)
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


class FtrackShotProcessorPreset(hiero.core.ProcessorPreset, FtrackBase):

    def __init__(self, name, properties, task=FtrackShotProcessor):

        super(FtrackShotProcessorPreset, self).__init__(
            task, name
        )

        self.properties()['processors'] = []
        self.properties()['exportRoot'] = '/usr/tmp'
        self.properties()['exportTemplate'] = ''
        self.properties().update(properties)

    def supportedItems(self):
        return hiero.core.TaskPresetBase.kAllItems
