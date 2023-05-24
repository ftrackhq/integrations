# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero

from hiero.exporters.FnEDLExportTask import (
    EDLExportTask,
    EDLExportPreset
)
from hiero.exporters.FnEDLExportUI import EDLExportUI
from hiero.core.FnExporterBase import TaskCallbacks
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout

from ftrack_connect_nuke_studio.config import report_exception

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackEDLExporter(EDLExportTask, FtrackProcessor):
    '''EDL Task exporter.'''

    @report_exception
    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        EDLExportTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

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

    @report_exception
    def __init__(self, name, properties):
        '''Initialise task with *name* and *properties*.'''
        EDLExportPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackEDLExporter

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
        self.properties()['ftrack']['component_name'] = 'EDL'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)

    def addUserResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)

        resolver.addResolver(
            "{sequence}",
            "Name of the sequence being processed",
            lambda keyword, task: task.sequenceName()
        )


class FtrackEDLExporterUI(EDLExportUI, FtrackProcessorUI):
    '''EDL Task Ui.'''

    @report_exception
    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        EDLExportUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack EDL Exporter'
        self._taskType = FtrackEDLExporter

    def populateUI(self, widget, exportTemplate):
        EDLExportUI.populateUI(self, widget, exportTemplate)
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Ftrack Options')
        self.addFtrackTaskUI(form_layout, exportTemplate)


hiero.core.taskRegistry.registerTask(FtrackEDLExporterPreset, FtrackEDLExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackEDLExporterPreset, FtrackEDLExporterUI)