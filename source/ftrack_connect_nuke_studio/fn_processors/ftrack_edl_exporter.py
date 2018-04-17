import re
import hiero.core
from hiero.exporters.FnEDLExportTask import (
    EDLExportTask,
    EDLExportPreset
)

from hiero.exporters.FnEDLExportUI import EDLExportUI

from ftrack_base import FtrackBasePreset, FtrackBase, FtrackBaseProcessor


class FtrackEDLExporter(EDLExportTask, FtrackBaseProcessor):
    def __init__(self, initDict):
        EDLExportTask.__init__(self, initDict)
        FtrackBaseProcessor.__init__(self, initDict)

    def startTask(self):
        self.create_project_structure()
        EDLExportTask.startTask(self)

    def finishTask(self):
        FtrackBaseProcessor.finishTask(self)
        EDLExportTask.finishTask(self)

    def _makePath(self):
        # disable making file paths
        FtrackBaseProcessor._makePath(self)


class FtrackEDLExporterPreset(EDLExportPreset, FtrackBasePreset):
    def __init__(self, name, properties):
        EDLExportPreset.__init__(self, name, properties)
        FtrackBasePreset.__init__(self, name, properties)
        self._parentType = FtrackEDLExporter

        # Update preset with loaded data
        self.properties().update(properties)

    def set_ftrack_properties(self, properties):
        FtrackBasePreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})
        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['task_type'] = 'Editing'
        self.properties()['ftrack']['asset_type_code'] = 'edl'
        self.properties()['ftrack']['component_name'] = 'main'
        self.properties()['ftrack']['component_pattern'] = '.{ext}'
        self.properties()['ftrack']['opt_publish_thumbnail'] = False

    def addUserResolveEntries(self, resolver):
        FtrackBasePreset.addFtrackResolveEntries(self, resolver)
        EDLExportPreset.addCustomResolveEntries(self, resolver)


class FtrackEDLExporterUI(EDLExportUI, FtrackBase):
    def __init__(self, preset):
        EDLExportUI.__init__(self, preset)
        FtrackBase.__init__(self, preset)

        self._displayName = "Ftrack EDL Exporter"
        self._taskType = FtrackEDLExporter


hiero.core.taskRegistry.registerTask(FtrackEDLExporterPreset, FtrackEDLExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackEDLExporterPreset, FtrackEDLExporterUI)