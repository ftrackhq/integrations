# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from hiero.exporters.FnAudioExportTask import AudioExportTask, AudioExportPreset
from hiero.exporters.FnAudioExportUI import AudioExportUI
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout


from ftrack_connect_nuke_studio.config import report_exception

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackAudioExporter(AudioExportTask, FtrackProcessor):
    '''Audio Task exporter.'''

    @report_exception
    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        AudioExportTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def startTask(self):
        '''Override startTask.'''
        AudioExportTask.startTask(self)

    def _makePath(self):
        '''Disable file path creation.'''
        pass


class FtrackAudioExporterPreset(AudioExportPreset, FtrackProcessorPreset):
    '''Audio Task preset.'''

    @report_exception
    def __init__(self, name, properties):
        '''Initialise task with *name* and *properties*.'''
        AudioExportPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackAudioExporter

        # Update preset with loaded data
        self.properties().update(properties)
        self.setName(self.properties()['ftrack']['component_name'])

    def name(self):
        '''Return task/component name.'''
        return self.properties()['ftrack']['component_name']

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for task.'''
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['component_pattern'] = '.{ext}'
        self.properties()['ftrack']['component_name'] = 'Audio'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)

    def addCustomResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)
        # ensure to have {ext} set to a wav fixed extension
        resolver.addResolver('{ext}', 'Extension of the file to be output', 'wav')

        # Provide common resolver from ShotProcessorPreset
        resolver.addResolver(
            "{clip}",
            "Name of the clip used in the shot being processed",
            lambda keyword, task: task.clipName()
        )

        resolver.addResolver(
            "{shot}",
            "Name of the shot being processed",
            lambda keyword, task: task.shotName()
        )

        resolver.addResolver(
            "{track}",
            "Name of the track being processed",
            lambda keyword, task: task.trackName()
        )

        resolver.addResolver(
            "{sequence}",
            "Name of the sequence being processed",
            lambda keyword, task: task.sequenceName()
        )


class FtrackAudioExporterUI(AudioExportUI, FtrackProcessorUI):
    '''Audio Task Ui.'''

    @report_exception
    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        AudioExportUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Audio Exporter'
        self._taskType = FtrackAudioExporter

    def populateUI(self, widget, exportTemplate):
        AudioExportUI.populateUI(self, widget, exportTemplate)
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Ftrack Options')

        self.addFtrackTaskUI(form_layout, exportTemplate)

hiero.core.taskRegistry.registerTask(FtrackAudioExporterPreset, FtrackAudioExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackAudioExporterPreset, FtrackAudioExporterUI)