# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile
import os
from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessor import ShotProcessor, ShotProcessorPreset

 

class FtrackShotProcessor(ShotProcessor, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBase.__init__(self)

    def create_project_structure(self, task):
        for (export_path, preset) in self._exportTemplate.flatten():
            preset_name = preset.name()
            path = task.resolvePath(export_path)
            for template, token in zip(export_path.split(os.path.sep), path.split(os.path.sep)):
                self.logger.info('%s , %s ' % (template, token))
    
            self.logger.info('creating structure for :{0} against {1}'.format(preset_name, path))


    def processTaskPreQueue(self):
        super(FtrackShotProcessor, self).processTaskPreQueue()
        for taskGroup in self._submission.children():
            for task in taskGroup.children():
                self.logger.info('Processing Task pre queue: %s' % task)
                self.create_project_structure(task)

    # def startProcessing(self, exportItems, preview=False):
    #     if not preview:
    #         self.logger.info('!!!!!!!!!! Processing: %s, is preview %s' % (exportItems, preview))
    #     # if not preview:.....
    #     # for item in exportItems:
    #     #     self.create_project_structure(item)

    #     result = super(FtrackShotProcessor, self).startProcessing(exportItems, preview=preview)
    #     if not preview:
    #         self.logger.info('!!!!!!!!!! Processing: DONE')

    #     return result

class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackBase):

    def __init__(self, name, properties):
        super(FtrackShotProcessorPreset, self).__init__(
            name, properties
        )
        FtrackBase.__init__(self)
        self._parentType = FtrackShotProcessor
        self.set_export_root()

    def set_export_root(self):
        accessor_prefix = self.ftrack_location.accessor.prefix
        self.properties()["exportRoot"] = accessor_prefix

    def addUserResolveEntries(self, resolver):
        
        resolver.addResolver(
            "{ftrack_project}",
            "Ftrack project path.",
            lambda keyword, task: self.resolve_ftrack_project(task)
        )

        resolver.addResolver(
            "{ftrack_sequence}",
            "Ftrack sequence path.",
            lambda keyword, task: self.resolve_ftrack_sequence(task)
        )

        resolver.addResolver(
            "{ftrack_shot}",
            "Ftrack shot path.",
            lambda keyword, task: self.resolve_ftrack_shot(task)
        )

        resolver.addResolver(
            "{ftrack_task}",
            "Ftrack task path.",
            lambda keyword, task: self.resolve_ftrack_task(task)
        )

        resolver.addResolver(
            "{ftrack_component}",
            "Ftrack component path.",
            lambda keyword, task: self.resolve_ftrack_component(task)
        )

        resolver.addResolver(
            "{ftrack_version}",
            "Ftrack version.",
            lambda keyword, task: self.resolve_ftrack_version(task)
        )