# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from hiero.exporters.FnAudioExportTask import AudioExportTask, AudioExportPreset
from hiero.exporters.FnAudioExportUI import AudioExportUI

from ftrack_connect_nuke_studio_beta.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackAudioExporter(AudioExportTask, FtrackProcessor):
    '''Audio Task exporter class.'''

    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''

        AudioExportTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def startTask(self):
        '''Override startTask.'''
        AudioExportTask.startTask(self)

    def _makePath(self):
        '''Disable file path creation.'''
        pass


class FtrackAudioExporterPreset(AudioExportPreset, FtrackProcessorPreset):
    '''Audio Task preset class.'''

    def __init__(self, name, properties):
        '''Initialise task with *name* and *properties*.'''

        AudioExportPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackAudioExporter

        # Update preset with loaded data
        self.properties().update(properties)

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for task.'''

        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['component_pattern'] = '.{ext}'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)

    def addCustomResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''

        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)
        # ensure to have {ext} set to a wav fixed extension
        resolver.addResolver('{ext}', 'Extension of the file to be output', 'wav')


class FtrackAudioExporterUI(AudioExportUI, FtrackProcessorUI):
    '''Audio Task Ui.'''

    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        AudioExportUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Audio Exporter'
        self._taskType = FtrackAudioExporter


hiero.core.taskRegistry.registerTask(FtrackAudioExporterPreset, FtrackAudioExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackAudioExporterPreset, FtrackAudioExporterUI)