# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from hiero.exporters.FnTimelineProcessor import TimelineProcessor
from hiero.exporters.FnTimelineProcessor import TimelineProcessorPreset
from hiero.exporters.FnTimelineProcessorUI import TimelineProcessorUI

from QtExt import QtWidgets

from ftrack_connect_nuke_studio_beta.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset, FtrackProcessor, FtrackProcessorUI
)


class FtrackTimelineProcessor(TimelineProcessor, FtrackProcessor):
    def __init__(self, preset, submission, synchronous=False):
        '''Initialise processor with *preset* , *submission* and option to run as *synchronous*.'''
        TimelineProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackProcessor.__init__(self, preset)

    def startProcessing(self, exportItems, preview=False):
        ''' Start processing of *exportItems* with optional *preview* mode. '''
        result = FtrackProcessor.validate_ftrack_processing(self, exportItems, preview)
        if result:
            exportItems = self.create_project_structure(exportItems)
        return TimelineProcessor.startProcessing(self, exportItems, preview)


class FtrackTimelineProcessorUI(TimelineProcessorUI, FtrackProcessorUI):

    def __init__(self, preset):
        '''Initialise processor ui with *preset*.'''
        TimelineProcessorUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

    def updatePathPreview(self):
        ''' Override path preview widget to show ftrack server address.'''
        self._pathPreviewWidget.setText('Ftrack Server: {0}'.format(self.session.server_url))

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
        return 'Ftrack Timeline Processor'

    def toolTip(self):
        ''' Return processor tooltip. '''
        return 'Process as Shots generates output on a per shot basis.'

    def populateUI(self, processorUIWidget, taskUIWidget, exportItems):
        '''Populate processor ui with *exportItems*, with parent widget *processorUIWidget* or *taskUIWidget*.'''
        TimelineProcessorUI.populateUI(self, processorUIWidget, taskUIWidget, exportItems)
        FtrackProcessorUI.addFtrackProcessorUI(self, processorUIWidget, exportItems)


class FtrackTimelineProcessorPreset(TimelineProcessorPreset, FtrackProcessorPreset):

    def __init__(self, name, properties):
        '''Initialise processor preset with *name* and *properties*.'''
        TimelineProcessorPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackTimelineProcessor

    def addCustomResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for processor.'''
        FtrackProcessorPreset.set_ftrack_properties(self, properties)

        # add placeholders for default task properties
        self.properties()['ftrack']['task_type'] = 'Editing'

        # set asset name for processor
        self.properties()['ftrack']['asset_name'] = 'Ingest'

        # asset type for processor
        self.properties()['ftrack']['asset_type_code'] = 'edl'


# Register the ftrack sequence processor.
hiero.ui.taskUIRegistry.registerProcessorUI(
    FtrackTimelineProcessorPreset, FtrackTimelineProcessorUI
)

hiero.core.taskRegistry.registerProcessor(
    FtrackTimelineProcessorPreset, FtrackTimelineProcessor
)