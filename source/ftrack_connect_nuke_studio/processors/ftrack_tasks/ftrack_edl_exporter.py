# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import opentimelineio as otio
import logging
import hiero

from hiero.exporters.FnEDLExportTask import (
    EDLExportTask,
    EDLExportPreset
)
from hiero.exporters.FnEDLExportUI import EDLExportUI
from hiero.exporters.FnEDLExportTask import EDLExportTask, EDLExportTrackTask
from hiero.core.FnExporterBase import TaskCallbacks
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.core import Transition

from ftrack_connect_nuke_studio.config import report_exception

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class OTIOExportTrackTask(EDLExportTrackTask):
    def __init__(self, parent, track, trackItems):
        EDLExportTrackTask.__init__(self, parent, track, trackItems)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._otio_track = otio.schema.Track()
        self._otio_track.name = track.name()
        self._otio_track.metadata = track.metadata().dict()

    def createClip(self, trackItem):
        sourceIn = trackItem.sourceIn()
        sourceOut = trackItem.sourceOut()

        clip_metadata = trackItem.metadata().dict()

        clip = otio.schema.Clip()
        clip.metadata = clip_metadata

        clip.name = trackItem.name()

        available_range = otio.opentime.TimeRange(
            otio.opentime.from_frames(sourceIn, self._fps),
            otio.opentime.from_frames(sourceOut - sourceIn , self._fps)
        )
        clip.source_range = available_range

        media_source = trackItem.source().mediaSource()
        if media_source:
            media_metadata = media_source.metadata().dict()
            media_file = media_source.fileinfos()[0]
            media_file_path = media_file.filename()
            clip.media_reference = otio.schema.ExternalReference()
            clip.media_reference.name = media_source.filename()
            clip.media_reference.target_url = media_file_path
            clip.media_reference.metadata = media_metadata

            media_range = otio.opentime.TimeRange(
                otio.opentime.from_frames(media_file.startFrame(), self._fps),
                otio.opentime.from_frames(media_file.endFrame() - media_file.startFrame(), self._fps)
            )
            clip.media_reference.available_range = media_range

        self.logger.info(
            'Adding clip {} to track {}'.format(clip, self._otio_track)
        )
        self._otio_track.append(clip)

    def createFadeIn(self, trackItem):
        pass

    def createFadeOut(self, trackItem):
        pass

    def createTransitionTo(self, trackItem, nextTrackItem):
        pass

    def taskStep(self):
        if len(self._trackItems) == 0:
            return False

        trackItem = self._trackItems[self._trackItemIndex]

        inTransition = trackItem.inTransition()
        outTransition = trackItem.outTransition()

        self.createClip(trackItem)

        if inTransition:
            if inTransition.alignment() is Transition.kFadeIn:
                self.createFadeIn(trackItem)
        if outTransition:
            if outTransition.alignment() is Transition.kFadeOut:
                self.createFadeOut(trackItem)
            else:
                nextTrackItem = self._trackItems[self._trackItemIndex + 1]
                self.createTransitionTo(trackItem, nextTrackItem)

        self._eventIndex += 1
        self._trackItemIndex += 1

        return self._trackItemIndex < len(self._trackItems)


class FtrackEDLExporter(EDLExportTask, FtrackProcessor):
    '''EDL Task exporter.'''

    @report_exception
    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        EDLExportTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)
        self.timeline = otio.schema.Timeline()

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def startTask(self):
        '''Override startTask.'''
        # foundry forgot to call the superclass....so we do it.
        TaskCallbacks.call(TaskCallbacks.onTaskStart, self)

        try:
            # Build list of items from sequence to be added added to the EDL
            for track in self._sequence.videoTracks():
                trackItems = []
                for trackitem in track:
                    trackItems.append(trackitem)
                    self._stepTotal += 1

                # We shouldn't get passed any empty tracks but if we do, don't create a task for them
                if trackItems:
                    task = OTIOExportTrackTask(self, track, trackItems)
                    self.logger.info('adding {} to {}'.format(task._otio_track, self.timeline))
                    self.timeline.tracks.append(task._otio_track)
                    self._trackTasks.append(task)

        except Exception, e:
            self.setError(str(e))

    def taskStep(self):
        try:
            trackTask = self._trackTasks[self._trackTaskIndex]
            self._currentTrack = trackTask._track

            if not trackTask.taskStep():
                path = self.exportFilePath()

                otio.core.serialize_json_to_file(self.timeline, path)
                self._trackTaskIndex += 1

            self._stepCount += 1
            return self._stepCount < self._stepTotal
        except Exception, e:
            self.setError(str(e))
            self.logger.exception(e)
            return False

    def _makePath(self):
        '''Disable file path creation.'''
        pass

    def exportFilePath(self):
        exportPath = self.resolvedExportPath()
        # Check file extension
        if not exportPath.lower().endswith(".otio"):
            exportPath += ".otio"
        return exportPath


class FtrackEDLExporterPreset(EDLExportPreset, FtrackProcessorPreset):
    '''EDL Task preset.'''

    def supportsAudio(self):
        return False

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

    def addCustomResolveEntries(self, resolver):
        EDLExportPreset.addCustomResolveEntries(self, resolver)
        resolver.addResolver("{ext}", "Extension of the file to be output", lambda keyword, task: "otio")


class FtrackEDLExporterUI(EDLExportUI, FtrackProcessorUI):
    '''EDL Task Ui.'''

    @report_exception
    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''
        EDLExportUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack OTIO-EDL Exporter'
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