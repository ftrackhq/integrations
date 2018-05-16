# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import time

import hiero

from hiero.exporters.FnEDLExportTask import (
    EDLExportTask,
    EDLExportPreset
)
from hiero.exporters.FnEDLExportUI import EDLExportUI

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import FtrackProcessorPreset, FtrackProcessor, FtrackProcessorUI


class FtrackEDLExporter(EDLExportTask, FtrackProcessor):
    def __init__(self, initDict):
        EDLExportTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def startTask(self):
        self.create_project_structure()
        track = self._item
        localtime = time.localtime(time.time())

        self.addFtrackTag(track, localtime)
        EDLExportTask.startTask(self)

    def finishTask(self):
        FtrackProcessor.finishTask(self)
        EDLExportTask.finishTask(self)

    def _makePath(self):
        # disable making file paths
        FtrackProcessor._makePath(self)


class FtrackEDLExporterPreset(EDLExportPreset, FtrackProcessorPreset):
    def __init__(self, name, properties):
        EDLExportPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackEDLExporter

        # Update preset with loaded data
        self.properties().update(properties)

    def set_ftrack_properties(self, properties):
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})
        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['task_type'] = 'Editing'
        self.properties()['ftrack']['asset_type_code'] = 'edit'
        self.properties()['ftrack']['component_name'] = 'main'
        self.properties()['ftrack']['component_pattern'] = '.{ext}'
        self.properties()['ftrack']['opt_publish_thumbnail'] = False

    def addUserResolveEntries(self, resolver):
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)
        EDLExportPreset.addCustomResolveEntries(self, resolver)


class FtrackEDLExporterUI(EDLExportUI, FtrackProcessorUI):
    def __init__(self, preset):
        EDLExportUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack EDL Exporter'
        self._taskType = FtrackEDLExporter


hiero.core.taskRegistry.registerTask(FtrackEDLExporterPreset, FtrackEDLExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackEDLExporterPreset, FtrackEDLExporterUI)