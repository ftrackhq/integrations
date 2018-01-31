import hiero.core
import hiero.core.util
import hiero.core.nuke as nuke
import hiero.exporters
import _nuke # import _nuke so it does not conflict with hiero.core.nuke

from hiero.exporters.FnNukeShotExporter import NukeShotExporter, NukeShotPreset
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI

from hiero.exporters import FnShotExporter
from hiero.exporters import FnExternalRender
from hiero.exporters import FnScriptLayout



from ftrack_base import FtrackBase

class FtrackNukeShotExporter(NukeShotExporter, FtrackBase):
    def __init__(self, initDict):
        super(FtrackNukeShotExporter, self).__init__(initDict)

    def taskStep(self):
        self.logger.info('TaskStep...')
        super(FtrackNukeShotExporter, self).taskStep()

    def startTask(self):
        self.logger.info('Starting Task')
        return super(FtrackNukeShotExporter, self).startTask()
    
    def finishTask(self):
        self.logger.info('Finishing Task')
        super(FtrackNukeShotExporter, self).finishTask()


class FtrackNukeShotExporterPreset(NukeShotPreset, FtrackBase):
    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        super(FtrackNukeShotExporterPreset, self).__init__(name, properties, task)

        # Set any preset defaults here
        self.properties()["enable"] = True
        self.properties()["readPaths"] = []
        self.properties()["writePaths"] = []
        self.properties()["collateTracks"] = False
        self.properties()["collateShotNames"] = False
        self.properties()["annotationsPreCompPaths"] = []
        self.properties()["includeAnnotations"] = False
        self.properties()["showAnnotations"] = True
        self.properties()["includeEffects"] = True

        # If True, tracks other than the master one will not be connected to the write node
        self.properties()["connectTracks"] = False

        # Asset properties
        self.properties()["useAssets"] = True
        self.properties()["publishScript"] = True

        # Not exposed in UI
        self.properties()["collateSequence"] = False  # Collate all trackitems within sequence
        self.properties()["collateCustomStart"] = True  # Start frame is inclusive of handles

        self.properties()["additionalNodesEnabled"] = False
        self.properties()["additionalNodesData"] = []
        self.properties()["method"] = "Blend"

        # Add property to control whether the exporter does a postProcessScript call.
        # This is not in the UI, and is only changed by create_comp.  See where this is accessed
        # in _taskStep() for more details.
        self.properties()["postProcessScript"] = True

        # Update preset with loaded data
        self.properties().update(properties)


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackBase):
    def __init__(self, preset):
        super(FtrackNukeShotExporterUI, self).__init__(preset)
        self._displayName = "Ftrack Nuke Shot File"
        self._taskType = FtrackNukeShotExporter

    def populateUI(self, widget, exportTemplate):
        super(FtrackNukeShotExporterUI, self).populateUI(widget, exportTemplate)


hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
