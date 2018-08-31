# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging
import os
import re
import copy
import hiero
import hiero.core.util
from hiero.ui.FnUIProperty import UIPropertyFactory
import tempfile

from hiero.exporters.FnSubmission import Submission
from hiero.exporters.FnTranscodeExporter import TranscodeExporter, TranscodePreset
from hiero.exporters.FnTranscodeExporterUI import TranscodeExporterUI
from hiero.exporters.FnExternalRender import NukeRenderTask

from ftrack_connect_nuke_studio_beta.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackReviewableExporter(TranscodeExporter, FtrackProcessor):
    '''Reviewable Task exporter.'''

    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        NukeRenderTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
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
        path = tempfile.NamedTemporaryFile(suffix='.nk').name
        dirname, filename = os.path.split(path)
        root, ext = os.path.splitext(filename)

        percentmatch = re.search('%\d+d', root)
        if percentmatch:
            percentpad = percentmatch.group()
            root = root.replace(percentpad, '')

        self._root = dirname + '/' + root.rstrip('#').rstrip('.')

        scriptExtension = '.nknc' if hiero.core.isNC() else '.nk'
        self._scriptfile = str(self._root + scriptExtension)

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

    def updateItem(self, originalItem, localtime):
        '''Override to inject new trascode script.'''
        self.createTranscodeScript()

    def _makePath(self):
        '''Disable file path creation.'''
        pass


class FtrackReviewableExporterPreset(TranscodePreset, FtrackProcessorPreset):
    '''Reviewable Task preset.'''

    def __init__(self, name, properties):
        '''Initialise task with *name* and *properties*.'''
        TranscodePreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackReviewableExporter

        # Update preset with loaded data
        self.properties().update(properties)
        self.setName(self.properties()['ftrack']['task_name'])

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for task.'''
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['component_pattern'] = '.mov'
        self.properties()['ftrack']['task_name'] = 'Reviewable'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)

        # enforce mov for newly created task
        self.properties()['file_type'] = 'mov'
        self.properties()['mov'] = {
                'encoder': 'mov64',
                'codec': 'avc1\tH.264',
                'quality': 3,
                'settingsString': 'H.264, High Quality',
                'keyframerate': 1,
        }

    def addUserResolveEntries(self, resolver):
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)


class FtrackReviewableExporterUI(TranscodeExporterUI, FtrackProcessorUI):
    '''Reviewable Task Ui.'''

    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        TranscodeExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Reviewable Render'
        self._taskType = FtrackReviewableExporter

    def populateUI(self, widget, exportTemplate):
        TranscodeExporterUI.populateUI(self, widget, exportTemplate)
        self.addFtrackTaskUI(widget, exportTemplate)


hiero.core.taskRegistry.registerTask(FtrackReviewableExporterPreset, FtrackReviewableExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackReviewableExporterPreset, FtrackReviewableExporterUI)
