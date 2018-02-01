# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile
import types
import os
import hiero
import time
import hiero.core
import hiero.ui
from hiero import core

from hiero.exporters.FnShotProcessor import ShotProcessorPreset
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.exporters.FnShotProcessor import buildTagsData, findTrackItemExportTag, getShotNameIndex
from hiero.exporters.FnEffectHelpers import ensureEffectsNodesCreated
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI

from hiero.ui.FnTagFilterWidget import TagFilterWidget
from hiero.core.FnProcessor import _expandTaskGroup

from QtExt import QtCore, QtWidgets
from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from .ftrack_base import FtrackBaseProcessor, FtrackBaseProcessorPreset, FtrackBaseProcessorUI


class FtrackShotProcessor(ShotProcessor, FtrackBaseProcessor):
    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBaseProcessor.__init__(self, preset, submission, synchronous=synchronous)


class FtrackShotProcessorUI(ShotProcessorUI, FtrackBaseProcessorUI):

    def __init__(self, preset):
        ShotProcessorUI.__init__(self, preset)
        FtrackBaseProcessorUI.__init__(self, preset)

    def displayName(self):
        return "Ftrack"

    def toolTip(self):
        return "Process as Shots generates output on a per shot basis."

    def updatePathPreview(self):
        self._pathPreviewWidget.setText('Ftrack Server: {0}'.format(self.session.server_url))


class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackBaseProcessorPreset):
    def __init__(self, name, properties):
        ShotProcessorPreset.__init__(self, name, properties)
        FtrackBaseProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackShotProcessor