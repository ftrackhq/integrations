import hiero.core.util
from hiero.exporters.FnNukeShotExporter import NukeShotExporter, NukeShotPreset
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI


from ftrack_base import FtrackBasePreset, FtrackBase, FtrackBaseProcessor


class FtrackNukeShotExporter(NukeShotExporter, FtrackBaseProcessor):
    def __init__(self, initDict):
        NukeShotExporter.__init__(self, initDict)
        FtrackBaseProcessor.__init__(self, initDict)

    def startTask(self):
        self.logger.info('----------- Start Task -----------')
        FtrackBaseProcessor.startTask(self)
        NukeShotExporter.startTask(self)

    def finishTask(self):
        self.logger.info('----------- Finish Task -----------')
        FtrackBaseProcessor.finishTask(self)
        NukeShotExporter.finishTask(self)

    def _makePath(self):
        # disable making file paths
        FtrackBaseProcessor._makePath(self)

    def _beforeNukeScriptWrite(self, script):
        self.logger.info('----------- beforeNukeScriptWrite -----------')
        # here we can add ftrack related nodes to the script
        NukeShotExporter._beforeNukeScriptWrite(self, script)


class FtrackNukeShotExporterPreset(NukeShotPreset, FtrackBasePreset):
    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        NukeShotPreset.__init__(self, name, properties, task)
        FtrackBasePreset.__init__(self, name, properties)

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
        
    def set_ftrack_properties(self, properties):
        FtrackBasePreset.set_ftrack_properties(self, properties)
        self.properties()['ftrack'] = {}

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['task_type'] = 'Compositing'
        self.properties()['ftrack']['asset_type_code'] = 'nuke_scene'
        self.properties()['ftrack']['component_pattern'] = '.{ext}'
        self.properties()['ftrack']['task_status'] = 'Not Started'
        self.properties()['ftrack']['shot_status'] = 'In progress'
        self.properties()['ftrack']['asset_version_status'] = 'WIP'
        self.properties()['ftrack']['project_schema'] = 'Film Pipeline'

    def addUserResolveEntries(self, resolver):
        FtrackBasePreset.addUserResolveEntries(self, resolver)
        NukeShotPreset.addUserResolveEntries(self, resolver)


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackBase):
    def __init__(self, preset):
        NukeShotExporterUI.__init__(self, preset)
        FtrackBase.__init__(self, preset)

        self._displayName = "Ftrack Nuke Shot File"
        self._taskType = FtrackNukeShotExporter
        self._nodeSelectionWidget = None


hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
