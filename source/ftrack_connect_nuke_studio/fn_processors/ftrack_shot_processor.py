# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile

from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessor import ShotProcessor, ShotProcessorPreset


class FtrackShotProcessor(ShotProcessor, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBase.__init__(self)

    def create_structure_fragment(self, item):
        self.logger.info('creating structure for :{0}'.format(item.trackItem()))

    def startProcessing(self, exportItems, preview=False):
        self.logger.info('!!!!!!!!!! Processing: %s' % (exportItems))
        for item in exportItems:
            self.create_structure_fragment(item)
        super(FtrackShotProcessor, self).startProcessing(exportItems, preview=preview)


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

    def resolve_ftrack_path(self, task):
        trackItem = task._item
         # for now just resolve agains the track name
        self.logger.info(trackItem.tags())
        return trackItem.name()
    
    def addUserResolveEntries(self, resolver):
        resolver.addResolver(
            "{ftrack}",
            "Ftrack managed path.",
            lambda keyword, task: self.resolve_ftrack_path(task)
        )

