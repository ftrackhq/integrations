# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from hiero.exporters.FnShotProcessor import ShotProcessorPreset
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI

from QtExt import QtWidgets

from ftrack_connect_nuke_studio_beta.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset, FtrackProcessor, FtrackProcessorUI
)


class FtrackShotProcessor(ShotProcessor, FtrackProcessor):
    '''Ftrack shot processor.'''

    def __init__(self, preset, submission, synchronous=False):
        '''Initialise processor with *preset* , *submission* and option to run as *synchronous*.'''
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackProcessor.__init__(self, preset)

    def startProcessing(self, exportItems, preview=False):
        ''' Start processing of *exportItems* with optional *preview* mode. '''
        result = FtrackProcessor.validate_ftrack_processing(self, exportItems, preview)
        if result:
            exportItems = self.create_project_structure(exportItems)
        return ShotProcessor.startProcessing(self, exportItems, preview)


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
        self._pathPreviewWidget.setText('Using Location: {0} With mount point: {1}'.format(location_name, mount_point))

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

    def populateUI(self, processorUIWidget, taskUIWidget, exportItems):
        '''Populate processor ui with *exportItems*, with parent widget *processorUIWidget* or *taskUIWidget*.'''
        ShotProcessorUI.populateUI(self, processorUIWidget, taskUIWidget, exportItems)
        FtrackProcessorUI.addFtrackProcessorUI(self, processorUIWidget, exportItems)


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

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for processor.'''
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        # add placeholders for default task properties
        self.properties()['ftrack']['task_type'] = 'Editing'

        # set asset name for processor
        self.properties()['ftrack']['asset_name'] = 'Conform'

        # asset type for processor
        self.properties()['ftrack']['asset_type_code'] = 'img'


# Register the ftrack shot processor.
hiero.ui.taskUIRegistry.registerProcessorUI(
    FtrackShotProcessorPreset, FtrackShotProcessorUI
)

hiero.core.taskRegistry.registerProcessor(
    FtrackShotProcessorPreset, FtrackShotProcessor
)
