# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from hiero.exporters.FnShotProcessor import ShotProcessorPreset
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI
from hiero.core.FnProcessor import _expandTaskGroup
from ftrack_connect_nuke_studio.config import report_exception

from Qt import QtWidgets

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset, FtrackProcessor, FtrackProcessorUI
)


class FtrackShotProcessor(ShotProcessor, FtrackProcessor):
    '''Ftrack shot processor.'''

    @report_exception
    def __init__(self, preset, submission, synchronous=False):
        '''Initialise processor with *preset* , *submission* and option to run as *synchronous*.'''
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackProcessor.__init__(self, preset)

    @report_exception
    def startProcessing(self, exportItems, preview=False):
        ''' Start processing of *exportItems* with optional *preview* mode. '''
        result = FtrackProcessor.validate_ftrack_processing(self, exportItems, preview)
        if result:
            exportItems = self.create_project_structure(exportItems)
        return ShotProcessor.startProcessing(self, exportItems, preview)

    def processTaskPreQueue(self):
        '''Walk Tasks in submission and mark any duplicates.'''
        components = {}
        self.logger.info('processing TaskPreQueue')
        for task in _expandTaskGroup(self._submission):
            target_task = task._item.name()
            component_name = task.component_name()
            components.setdefault(target_task, [])

            self.logger.info('components {}'.format(components))
            if component_name not in components[target_task]:
                components[target_task].append(component_name)
            else:
                self.logger.info('{} is duplicated component for {}'.format(component_name, target_task))
                task.setDuplicate()


class FtrackShotProcessorUI(ShotProcessorUI, FtrackProcessorUI):
    '''Ftrack shot processor Ui.'''

    def __init__(self, preset):
        '''Initialise processor ui with *preset*.'''
        ShotProcessorUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

    def updatePathPreview(self):
        ''' Override path preview widget to show ftrack server address.'''
        location_name = self.ftrack_location['name']
        mount_point = self.ftrack_location.accessor.prefix
        self._pathPreviewWidget.setText('Using Location: {0}, with mount point: {1}'.format(location_name, mount_point))

    def _checkExistingVersions(self, exportItems):
        ''' Override to disable internal version existence.'''
        return True

    def createVersionWidget(self):
        ''' Override to disable version widget.
        Return an empty QWidget.
        '''
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def displayName(self):
        ''' Return processor display name. '''
        return 'Ftrack Shot Processor'

    def toolTip(self):
        ''' Return processor tooltip. '''
        return 'Process as Shots generates output on a per shot basis.'

    @report_exception
    def populateUI(self, processorUIWidget, taskUIWidget, exportItems):
        '''Populate processor ui with *exportItems*, with parent widget *processorUIWidget* or *taskUIWidget*.'''
        ShotProcessorUI.populateUI(self, processorUIWidget, taskUIWidget, exportItems)
        form_layout = FtrackProcessorUI.addFtrackProcessorUI(self, processorUIWidget, exportItems)
        self.add_thumbnail_options(form_layout)
        self.add_reviewable_options(form_layout)


class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackProcessorPreset):
    '''Ftrack shot processor preset.'''

    def __init__(self, name, properties):
        '''Initialise processor preset with *name* and *properties*.'''
        ShotProcessorPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)

        self._parentType = FtrackShotProcessor

    def addCustomResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)
        ShotProcessorPreset.addCustomResolveEntries(self, resolver)

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

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for processor.'''
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        # add placeholders for default task properties
        self.properties()['ftrack']['task_type'] = 'Editing'

        # set asset name for processor
        self.properties()['ftrack']['asset_name'] = '{track}'

        # asset type for processor
        self.properties()['ftrack']['asset_type_name'] = 'Image Sequence'

    def isValid(self):
        '''Check if write nodes are present and valid.'''
        # Always handle as valid for our ftrack shot processors .
        return (True, '')


# Register the ftrack shot processor.
hiero.ui.taskUIRegistry.registerProcessorUI(
    FtrackShotProcessorPreset, FtrackShotProcessorUI
)

hiero.core.taskRegistry.registerProcessor(
    FtrackShotProcessorPreset, FtrackShotProcessor
)
