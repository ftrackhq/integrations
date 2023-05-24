# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import re
import copy
import tempfile

import hiero
import hiero.core.util
from hiero.exporters.FnSubmission import Submission
from hiero.exporters.FnTranscodeExporter import TranscodeExporter, TranscodePreset
from hiero.exporters.FnTranscodeExporterUI import TranscodeExporterUI
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout

from ftrack_connect_nuke_studio.config import report_exception

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackNukeRenderExporter(TranscodeExporter, FtrackProcessor):
    '''NukeRender Task exporter.'''

    @report_exception
    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''

        TranscodeExporter.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)
        self.createTranscodeScript()

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def addWriteNodeToScript(self, script, rootNode, framerate):
        '''Restore original function from parent class.'''
        TranscodeExporter.addWriteNodeToScript(self, script, rootNode, framerate)

    def createTranscodeScript(self):
        '''Create a custom transcode script for this task.'''
        # This code is taken from TranscodeExporter.__init__
        # in order to output the nuke file in the right place we need to override this.

        self._audioFile = None

        # Figure out the script location
        path = tempfile.NamedTemporaryFile(suffix='.nk', delete=False).name
        self._scriptfile = str(path)

        self._renderTask = None
        if self._submission is not None:
            # Pass the frame range through to the submission.  This is useful for rendering through the frame
            # server, otherwise it would have to evaluate the script to determine it.
            start, end = self.outputRange()
            submissionDict = copy.copy(self._init_dict)
            submissionDict['startFrame'] = start
            submissionDict['endFrame'] = end

            # Create a job on our submission to do the actual rendering.
            self._renderTask = self._submission.addJob(Submission.kNukeRender, submissionDict, self._scriptfile)

    def _makePath(self):
        '''Disable file path creation.'''
        pass


class FtrackNukeRenderExporterPreset(TranscodePreset, FtrackProcessorPreset):
    '''NukeRender Task preset.'''

    @report_exception
    def __init__(self, name, properties):
        '''Initialise task with *name* and *properties*.'''
        TranscodePreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackNukeRenderExporter

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
        self.properties()['ftrack']['component_pattern'] = '.%04d.{ext}'
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


class FtrackNukeRenderExporterUI(TranscodeExporterUI, FtrackProcessorUI):
    '''NukeRender Task Ui.'''

    @report_exception
    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        TranscodeExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Nuke Render'
        self._taskType = FtrackNukeRenderExporter

    def populateUI(self, widget, exportTemplate):
        TranscodeExporterUI.populateUI(self, widget, exportTemplate)
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Ftrack Options')
        self.addFtrackTaskUI(form_layout, exportTemplate)

hiero.core.taskRegistry.registerTask(FtrackNukeRenderExporterPreset, FtrackNukeRenderExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeRenderExporterPreset, FtrackNukeRenderExporterUI)
