# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from hiero.exporters.FnShotProcessor import ShotProcessorPreset
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI
from hiero.core.FnExporterBase import TaskCallbacks

from QtExt import QtWidgets

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import FtrackProcessorPreset, FtrackProcessor, FtrackProcessorUI




class FtrackShotProcessor(ShotProcessor, FtrackProcessor):
    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackProcessor.__init__(self, preset)

    def on_task_finished(self, *args, **kwargs):
        self.logger.info('TASK FINISHED')
        self.logger.info(args)
        self.logger.info(kwargs)

    def startProcessing(self, exportItems, preview=False):
        TaskCallbacks.addCallback(TaskCallbacks.onTaskFinish, self.on_task_finished)

        self.create_project_structure(exportItems)
        result = FtrackProcessor.validateFtrackProcessing(self, exportItems)
        if result:
            render_tasks = ShotProcessor.startProcessing(self, exportItems, preview)

            # self.publishResultComponents(render_tasks)



class FtrackShotProcessorUI(ShotProcessorUI, FtrackProcessorUI):

    def __init__(self, preset):
        ShotProcessorUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

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

    def displayName(self):
        return 'Ftrack Shot Processor'

    def toolTip(self):
        return 'Process as Shots generates output on a per shot basis.'

    def populateUI(self, processorUIWidget, taskUIWidget, exportItems):
        ShotProcessorUI.populateUI(self, processorUIWidget, taskUIWidget, exportItems)
        FtrackProcessorUI.addFtrackProcessorUI(self, processorUIWidget, exportItems)


class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackProcessorPreset):
    def __init__(self, name, properties):
        ShotProcessorPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackShotProcessor

    def addCustomResolveEntries(self, resolver):
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)


# Register the ftrack shot processor.
hiero.ui.taskUIRegistry.registerProcessorUI(
    FtrackShotProcessorPreset, FtrackShotProcessorUI
)

hiero.core.taskRegistry.registerProcessor(
    FtrackShotProcessorPreset, FtrackShotProcessor
)
