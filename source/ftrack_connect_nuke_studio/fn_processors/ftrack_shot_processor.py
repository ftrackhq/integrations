# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile

from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessor import ShotProcessor, ShotProcessorPreset
# from ftrack_export_structure import FtrackExportStructure

class FtrackShotProcessor(ShotProcessor, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBase.__init__(self)

    def create_structure_fragment(self, item):
        # here we can take the item , inspect it and build the structure fragment in ftrack server.
        # once done we can add a tag to check whether has already been built , also track teh result uuid ? 
        track_item = item.trackItem()
        tags = track_item.tags()
        self.logger.info('creating structure for :{0}, tags:{1}'.format(track_item, tags))


    def startProcessing(self, exportItems, preview=False):
        self.logger.info('!!!!!!!!!! Processing: %s' % (exportItems))
        for item in exportItems:
            self.create_structure_fragment(item)
        return super(FtrackShotProcessor, self).startProcessing(exportItems, preview=preview)

    # def setPreset ( self, preset ):
    #     self._preset = preset
    #     oldTemplate = self._exportTemplate
    #     self._exportTemplate = FtrackExportStructure()
    #     self._exportTemplate.restore(self._preset.properties()["exportTemplate"])
    #     if self._preset.properties()["exportRoot"] != "None":
    #         self._exportTemplate.setExportRootPath(self._preset.properties()["exportRoot"])


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

