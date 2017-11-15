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
        self._parentType = FtrackShotProcessor

    def addUserResolveEntries(self, resolver):
        resolver.addResolver(
            "{ftrack}",
            "Ftrack managed path.",
            lambda keyword, task: tempfile.gettempdir()
        )
