# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import hiero

from hiero.exporters.FnShotProcessor import ShotProcessorPreset
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI

from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import *

from QtExt import QtWidgets

from .ftrack_base import FtrackBaseProcessor, FtrackBaseProcessorPreset, FtrackBaseProcessorUI


class FtrackShotProcessor(ShotProcessor, FtrackBaseProcessor):
    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBaseProcessor.__init__(self, preset)


class FtrackShotProcessorUI(ShotProcessorUI, FtrackBaseProcessorUI):

    def __init__(self, preset):
        ShotProcessorUI.__init__(self, preset)
        FtrackBaseProcessorUI.__init__(self, preset)

    def displayName(self):
        return 'Ftrack Shot Processor'

    def toolTip(self):
        return 'Process as Shots generates output on a per shot basis.'

    def updatePathPreview(self):
        self._pathPreviewWidget.setText('Ftrack Server: {0}'.format(self.session.server_url))

    def _checkExistingVersions(self, exportItems):
        # disable version check as we handle this internally
        return True

    def createVersionWidget(self):
        # disable version widget
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget
    #
    # def populateUI(self, processorUIWidget, taskUIWidget, exportItems):
    #     ShotProcessorUI.populateUI(self, processorUIWidget, taskUIWidget, exportItems)
    #     self.addFtrackUI(processorUIWidget, exportItems)
    #
    # def addFtrackUI(self, widget, exportTemplate):
    #     formLayout = TaskUIFormLayout()
    #     layout = widget.layout()
    #     layout.addLayout(formLayout)
    #     formLayout.addDivider("Ftrack Options")
    #
    #     # ----------------------------------
    #     # Thumbanil generation
    #
    #     key, value, label = 'opt_publish_thumbnail', True, 'Publish Thumbnail'
    #     thumbnail_tooltip = 'Generate and upload thumbnail'
    #
    #     uiProperty = UIPropertyFactory.create(
    #         type(value),
    #         key=key,
    #         value=value,
    #         dictionary=self._preset.properties()['ftrack'],
    #         label=label + ":",
    #         tooltip=thumbnail_tooltip
    #     )
    #     formLayout.addRow(label + ":", uiProperty)
    #
    #     # ----------------------------------
    #     # Component Name
    #
    #     key, value, label = 'component_name', '', 'Component Name'
    #     component_tooltip = 'Set Component Name'
    #
    #     uiProperty = UIPropertyFactory.create(
    #         type(value),
    #         key=key,
    #         value=value,
    #         dictionary=self._preset.properties()['ftrack'],
    #         label=label + ":",
    #         tooltip=component_tooltip
    #     )
    #     formLayout.addRow(label + ":", uiProperty)



class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackBaseProcessorPreset):
    def __init__(self, name, properties):
        ShotProcessorPreset.__init__(self, name, properties)
        FtrackBaseProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackShotProcessor

    def addCustomResolveEntries(self, resolver):
        FtrackBaseProcessorPreset.addFtrackResolveEntries(self, resolver)


# Register the ftrack shot processor.
hiero.ui.taskUIRegistry.registerProcessorUI(
    FtrackShotProcessorPreset, FtrackShotProcessorUI
)

hiero.core.taskRegistry.registerProcessor(
    FtrackShotProcessorPreset, FtrackShotProcessor
)
