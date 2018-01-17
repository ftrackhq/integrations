# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile
import os
from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessor import ShotProcessor, ShotProcessorPreset



class FtrackShotProcessor(ShotProcessor, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBase.__init__(self)

    def create_server_structure(self, item):
        # here we can take the item , inspect it and build the structure fragment in ftrack server.
        # once done we can add a tag to check whether has already been built , also track teh result uuid ? 
        track_item = item.trackItem()
        tags = track_item.tags()
        self.logger.info('creating structure for :{0}, tags:{1}'.format(track_item, tags))

    def startProcessing(self, exportItems, preview=False):
        self.logger.info('!!!!!!!!!! Processing: %s' % (exportItems))
        for item in exportItems:
            self.create_server_structure(item)
        result =  super(FtrackShotProcessor, self).startProcessing(exportItems, preview=preview)
        self.logger.info('Processing results !!!!!!!!!!: %s' % (result))

        return result

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