# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from hiero.exporters.FnAudioExportTask import AudioExportTask, AudioExportPreset
from hiero.exporters.FnAudioExportUI import AudioExportUI

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import FtrackProcessorPreset, FtrackProcessor, FtrackProcessorUI


class FtrackAudioExporter(AudioExportTask, FtrackProcessor):

    def __init__(self, initDict):
        AudioExportTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def startTask(self):
        self.create_project_structure()
        AudioExportTask.startTask(self)

    def finishTask(self):
        FtrackProcessor.finishTask(self)
        AudioExportTask.finishTask(self)

    def _makePath(self):
        # disable making file paths
        FtrackProcessor._makePath(self)


class FtrackAudioExporterPreset(AudioExportPreset, FtrackProcessorPreset):

    def __init__(self, name, properties):
        AudioExportPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackAudioExporter

        # Update preset with loaded data
        self.properties().update(properties)

    def set_ftrack_properties(self, properties):
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['task_type'] = 'Editing'
        self.properties()['ftrack']['asset_type_code'] = 'audio'
        self.properties()['ftrack']['component_name'] = 'main'
        self.properties()['ftrack']['component_pattern'] = '.{ext}'
        self.properties()['ftrack']['opt_publish_thumbnail'] = False
        self.properties()['ftrack']['opt_publish_reviewable'] = False

    def addCustomResolveEntries(self, resolver):
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)
        # ensure to have {ext} set to a wav fixed extension
        resolver.addResolver('{ext}', 'Extension of the file to be output', 'wav')


class FtrackAudioExporterUI(AudioExportUI, FtrackProcessorUI):
    def __init__(self, preset):
        AudioExportUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Audio Exporter'
        self._taskType = FtrackAudioExporter


hiero.core.taskRegistry.registerTask(FtrackAudioExporterPreset, FtrackAudioExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackAudioExporterPreset, FtrackAudioExporterUI)