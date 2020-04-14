# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import hiero.core.util
from hiero.exporters.FnCopyExporter import CopyExporter, CopyPreset
from hiero.exporters.FnCopyExporterUI import CopyExporterUI

from ftrack_connect_nuke_studio.config import report_exception
from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackCopyExporter(CopyExporter, FtrackProcessor):

    @report_exception
    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        CopyExporter.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def _makePath(self):
        '''Disable file path creation.'''
        pass


class FtrackCopyExporterPreset(CopyPreset, FtrackProcessorPreset):
    '''Shot Task preset.'''

    @report_exception
    def __init__(self, name, properties):
        '''Initialise task with *name* and *properties*.'''
        CopyPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackCopyExporter

        # Update preset with loaded data
        self.properties().update(properties)
        self.setName(self.name())

    def name(self):
        '''Return task/component name.'''
        return self.properties()['ftrack']['component_name']

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for task.'''
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['component_pattern'] = '.%4d.{fileext}'
        self.properties()['ftrack']['component_name'] = 'Plate'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)

    def addUserResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)

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


class FtrackCopyExporterUI(CopyExporterUI, FtrackProcessorUI):
    '''Shot Task Ui.'''

    @report_exception
    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        CopyExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Copy Exporter'
        self._taskType = FtrackCopyExporter


hiero.core.taskRegistry.registerTask(FtrackCopyExporterPreset, FtrackCopyExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackCopyExporterPreset, FtrackCopyExporterUI)
