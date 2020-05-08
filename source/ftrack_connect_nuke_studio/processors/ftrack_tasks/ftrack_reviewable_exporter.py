# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging
import copy
import os
import hiero.core.util
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout

import tempfile

from hiero.exporters.FnSubmission import Submission
from hiero.exporters.FnTranscodeExporter import TranscodeExporter, TranscodePreset
from hiero.exporters.FnTranscodeExporterUI import TranscodeExporterUI
from hiero.exporters.FnExportUtil import writeSequenceAudioWithHandles


from ftrack_connect_nuke_studio.config import report_exception
from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)

from ftrack_connect_nuke_studio.base import FtrackBase
Base = FtrackBase()
hiero_version_tuple = Base.hiero_version_tuple



class FtrackReviewableExporter(TranscodeExporter, FtrackProcessor):
    '''Reviewable Task exporter.'''

    @report_exception
    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        TranscodeExporter.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)
        self.logger.info(hiero_version_tuple)

        self.createTranscodeScript()

    def setAudioExportSettings(self):
        '''method to perpare audio settings
        
        ''' 
        extension = '.wav'
        path = tempfile.NamedTemporaryFile(
            suffix=extension, delete=False
        ).name.replace('\\', '/')
        self._audioFile = str(path)

        if hiero_version_tuple >= (12, 1, 0):
            # this method is from nuke 12.1.0 on, hence we call super only in that case
            from hiero.exporters import FnAudioHelper
            FnAudioHelper.setAudioExportSettings(self)

    def writeAudio(self):
        '''Override write audio method 
        This override allows to leverage the difference between versions.
        '''
        self.setAudioExportSettings()

        if isinstance(self._item, (hiero.core.Sequence, hiero.core.TrackItem)):
            if self._sequenceHasAudio(self._sequence):

                if isinstance(self._item, hiero.core.Sequence):
                    start, end = self.outputRange()
                    if hiero_version_tuple < (12, 1, 0):
                        audio_export_data = (
                            self._audioFile, start, end
                        )
                    else:
                        audio_export_data = (
                            self._audioFile, start, end,
                            self._outputChannels,
                            self._sampleRate,
                            self._bitDepth,
                            self._bitRate

                        )
                    self._item.writeAudioToFile(*audio_export_data)

                elif isinstance(self._item, hiero.core.TrackItem):
                    startHandle, endHandle = self.outputHandles()

                    if hiero_version_tuple < (12, 1, 0):
                        audio_export_data = (
                            self._audioFile,
                            self._sequence,
                            self._item.timelineIn(),
                            self._item.timelineOut(),
                            startHandle,
                            endHandle
                        )
                    else:
                        audio_export_data = (
                            self._audioFile,
                            self._sequence,
                            self._item.timelineIn(),
                            self._item.timelineOut(),
                            startHandle,
                            endHandle,
                            self._outputChannels,
                            self._sampleRate,
                            self._bitDepth,
                            self._bitRate
                        )

                    writeSequenceAudioWithHandles(*audio_export_data)

        if isinstance(self._item, hiero.core.Clip):
            if self._item.mediaSource().hasAudio():
                # If clip, write out full length
                if hiero_version_tuple < (12, 1, 0):
                    audio_export_data = (
                        self._audioFile
                    )

                else:
                    audio_export_data = (
                        self._audioFile,
                        self._outputChannels,
                        self._sampleRate,
                        self._bitDepth,
                        self._bitRate
                    )
                self._item.writeAudioToFile(*audio_export_data)

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def addWriteNodeToScript(self, script, rootNode, framerate):
        '''Restore original function from parent class.'''
        TranscodeExporter.addWriteNodeToScript(self, script, rootNode, framerate)

    def createTranscodeScript(self):
        '''Create a custom transcode script for this task.'''

        # Figure out the script location
        path = tempfile.NamedTemporaryFile(suffix='.nk', delete=False).name.replace('\\', '/')
        self._scriptfile = str(path)

        self.logger.debug('writing script to : {}'.format(self._scriptfile))

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


class FtrackReviewableExporterPreset(TranscodePreset, FtrackProcessorPreset):
    '''Reviewable Task preset.'''

    @report_exception
    def __init__(self, name, properties):
        '''Initialise task with *name* and *properties*.'''
        TranscodePreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackReviewableExporter

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
        self.properties()['ftrack']['component_pattern'] = '.mov'
        self.properties()['ftrack']['component_name'] = 'Reviewable'
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


class FtrackReviewableExporterUI(TranscodeExporterUI, FtrackProcessorUI):
    '''Reviewable Task Ui.'''

    @report_exception
    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        TranscodeExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Reviewable Render'
        self._taskType = FtrackReviewableExporter

    def populateUI(self, widget, exportTemplate):
        TranscodeExporterUI.populateUI(self, widget, exportTemplate)
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Ftrack Options')

        self.addFtrackTaskUI(form_layout, exportTemplate)


hiero.core.taskRegistry.registerTask(FtrackReviewableExporterPreset, FtrackReviewableExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackReviewableExporterPreset, FtrackReviewableExporterUI)
