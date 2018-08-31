# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import time

import hiero

from hiero.exporters.FnEDLExportTask import (
    EDLExportTask,
    EDLExportPreset
)
from hiero.exporters.FnEDLExportUI import EDLExportUI
from hiero.core.FnExporterBase import TaskCallbacks

from ftrack_connect_nuke_studio_beta.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackEDLExporter(EDLExportTask, FtrackProcessor):
    '''EDL Task exporter.'''

    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        EDLExportTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def startTask(self):
        '''Override startTask.'''
        # foundry forgot to call the superclass....so we do it.
        TaskCallbacks.call(TaskCallbacks.onTaskStart, self)
        EDLExportTask.startTask(self)

    def _makePath(self):
        '''Disable file path creation.'''
        pass


class FtrackEDLExporterPreset(EDLExportPreset, FtrackProcessorPreset):
    '''EDL Task preset.'''

    def __init__(self, name, properties):
        '''Initialise task with *name* and *properties*.'''
        EDLExportPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackEDLExporter

        # Update preset with loaded data
        self.properties().update(properties)
        self.setName(self.properties()['ftrack']['task_name'])

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for task.'''
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['component_pattern'] = '.{ext}'
        self.properties()['ftrack']['task_name'] = 'EDL'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)

    def addUserResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)


class FtrackEDLExporterUI(EDLExportUI, FtrackProcessorUI):
    '''EDL Task Ui.'''

    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        EDLExportUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack EDL Exporter'
        self._taskType = FtrackEDLExporter

    def populateUI(self, widget, exportTemplate):
        EDLExportUI.populateUI(self, widget, exportTemplate)
        self.addFtrackTaskUI(widget, exportTemplate)


hiero.core.taskRegistry.registerTask(FtrackEDLExporterPreset, FtrackEDLExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackEDLExporterPreset, FtrackEDLExporterUI)