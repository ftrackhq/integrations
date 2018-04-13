import hiero.core.util
from hiero.exporters.FnTranscodeExporter import TranscodeExporter, TranscodePreset
from hiero.exporters.FnTranscodeExporterUI import TranscodeExporterUI
from hiero.exporters.FnSubmission import Submission

from ftrack_base import FtrackBasePreset, FtrackBase, FtrackBaseProcessor


class FtrackNukeRenderExporter(TranscodeExporter, FtrackBaseProcessor):

    def __init__(self, initDict):
        TranscodeExporter.__init__(self, initDict)
        FtrackBaseProcessor.__init__(self, initDict)

    def updateItem(self, originalItem, localtime):
        TranscodeExporter.updateItem(self,  originalItem, localtime)
        FtrackBaseProcessor.updateItem(self, originalItem, localtime)

    def finishTask(self):
        FtrackBaseProcessor.finishTask(self)
        TranscodeExporter.finishTask(self)

    def _makePath(self):
        # disable making file paths
        FtrackBaseProcessor._makePath(self)


class FtrackNukeRenderExporterPreset(TranscodePreset, FtrackBasePreset):
    def __init__(self, name, properties):
        TranscodePreset.__init__(self, name, properties)
        FtrackBasePreset.__init__(self, name, properties)
        self._parentType = FtrackNukeRenderExporter

        # Update preset with loaded data
        self.properties().update(properties)

    def set_ftrack_properties(self, properties):
        FtrackBasePreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['task_type'] = 'Editing'
        self.properties()['ftrack']['asset_type_code'] = 'img'
        self.properties()['ftrack']['component_name'] = 'main'
        self.properties()['ftrack']['component_pattern'] = '.####.{ext}'

    def addUserResolveEntries(self, resolver):
        FtrackBasePreset.addUserResolveEntries(self, resolver)
        TranscodePreset.addCustomResolveEntries(self, resolver)


class FtrackNukeRenderExporterUI(TranscodeExporterUI, FtrackBase):
    def __init__(self, preset):
        TranscodeExporterUI.__init__(self, preset)
        FtrackBase.__init__(self, preset)

        self._displayName = "Ftrack Nuke Render"
        self._taskType = FtrackNukeRenderExporter
        self._nodeSelectionWidget = None


hiero.core.taskRegistry.registerTask(FtrackNukeRenderExporterPreset, FtrackNukeRenderExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeRenderExporterPreset, FtrackNukeRenderExporterUI)
