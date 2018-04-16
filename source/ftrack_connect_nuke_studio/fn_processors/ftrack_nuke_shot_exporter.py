import hiero.core.util
from hiero.exporters.FnNukeShotExporter import NukeShotExporter, NukeShotPreset
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI
from ftrack_base import FtrackBasePreset, FtrackBase, FtrackBaseProcessor


class FtrackNukeShotExporter(NukeShotExporter, FtrackBaseProcessor):

    def __init__(self, initDict):
        NukeShotExporter.__init__(self, initDict)
        FtrackBaseProcessor.__init__(self, initDict)

    def updateItem(self, originalItem, localtime):
        FtrackBaseProcessor.updateItem(self, originalItem, localtime)

    def finishTask(self):
        FtrackBaseProcessor.finishTask(self)
        NukeShotExporter.finishTask(self)

    def _makePath(self):
        # disable making file paths
        FtrackBaseProcessor._makePath(self)


class FtrackNukeShotExporterPreset(NukeShotPreset, FtrackBasePreset):
    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        NukeShotPreset.__init__(self, name, properties, task)
        FtrackBasePreset.__init__(self, name, properties)
        # Update preset with loaded data
        self.properties().update(properties)
        
    def set_ftrack_properties(self, properties):
        FtrackBasePreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})
        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['task_type'] = 'Compositing'
        self.properties()['ftrack']['asset_type_code'] = 'nuke_scene'
        self.properties()['ftrack']['component_name'] = 'main'
        self.properties()['ftrack']['component_pattern'] = '.{ext}'

    def addUserResolveEntries(self, resolver):
        FtrackBasePreset.addUserResolveEntries(self, resolver)
        NukeShotPreset.addUserResolveEntries(self, resolver)


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackBase):
    def __init__(self, preset):
        NukeShotExporterUI.__init__(self, preset)
        FtrackBase.__init__(self, preset)

        self._displayName = "Ftrack Nuke File"
        self._taskType = FtrackNukeShotExporter
        self._nodeSelectionWidget = None


hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
