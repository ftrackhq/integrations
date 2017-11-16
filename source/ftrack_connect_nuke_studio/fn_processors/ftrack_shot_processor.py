# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile

from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessor import ShotProcessor, ShotProcessorPreset


class FtrackShotProcessor(ShotProcessor, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        super(FtrackShotProcessor, self).__init__(
             preset, submission, synchronous=synchronous
        )


class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackBase):

    def __init__(self, name, properties):
        super(FtrackShotProcessorPreset, self).__init__(
            name, properties
        )
        FtrackBase.__init__(self)
        self._parentType = FtrackShotProcessor
        self.set_export_root()

    def set_export_root(self):
        self.properties()["exportRoot"] = '/tmp/'

    def resolve_ftrack_path(self, task):
        trackItem = task._item
         # for now just resolve agains the track name
        return trackItem.name()
    
    def addUserResolveEntries(self, resolver):
        resolver.addResolver(
            "{ftrack}",
            "Ftrack managed path.",
            lambda keyword, task: self.resolve_ftrack_path(task)
        )
