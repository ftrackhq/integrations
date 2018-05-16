# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
import hiero.core.util
from hiero.exporters.FnNukeShotExporter import NukeShotExporter, NukeShotPreset
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackNukeShotExporter(NukeShotExporter, FtrackProcessor):

    def __init__(self, initDict):
        NukeShotExporter.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def updateItem(self, originalItem, localtime):
        FtrackProcessor.updateItem(self, originalItem, localtime)

    def finishTask(self):
        FtrackProcessor.finishTask(self)
        NukeShotExporter.finishTask(self)

    def _makePath(self):
        # disable making file paths
        FtrackProcessor._makePath(self)


class FtrackNukeShotExporterPreset(NukeShotPreset, FtrackProcessorPreset):
    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        NukeShotPreset.__init__(self, name, properties, task)
        FtrackProcessorPreset.__init__(self, name, properties)
        # Update preset with loaded data
        self.properties().update(properties)
        
    def set_ftrack_properties(self, properties):
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})
        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['task_type'] = 'Compositing'
        self.properties()['ftrack']['asset_type_code'] = 'comp'
        self.properties()['ftrack']['component_name'] = 'main'
        self.properties()['ftrack']['component_pattern'] = '.{ext}'

    def addUserResolveEntries(self, resolver):
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackProcessorUI):
    def __init__(self, preset):
        NukeShotExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Nuke File'
        self._taskType = FtrackNukeShotExporter

    def populateUI(self, widget, exportTemplate):
        NukeShotExporterUI.populateUI(self, widget, exportTemplate)
        FtrackProcessorUI.addFtrackTaskUI(self, widget, exportTemplate)




hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
