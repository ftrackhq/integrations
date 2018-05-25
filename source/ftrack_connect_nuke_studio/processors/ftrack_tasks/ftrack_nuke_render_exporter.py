# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import re
import copy
from hiero.exporters.FnSubmission import Submission
from hiero.ui.FnUIProperty import UIPropertyFactory

import hiero
import hiero.core.util
from hiero.exporters.FnSubmission import Submission
from hiero.exporters.FnTranscodeExporter import TranscodeExporter, TranscodePreset
from hiero.exporters.FnTranscodeExporterUI import TranscodeExporterUI
from hiero.exporters.FnExternalRender import NukeRenderTask

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackNukeRenderExporter(TranscodeExporter, FtrackProcessor):

    def __init__(self, initDict):
        NukeRenderTask.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)

    def addWriteNodeToScript(self, script, rootNode, framerate):
        TranscodeExporter.addWriteNodeToScript(self, script, rootNode, framerate)

    def createTranscodeScript(self):
        # This code is taken from TranscodeExporter.__init__
        # in order to output the nuke file in the right place we need to override this.

        self._audioFile = None

        # Figure out the script location
        path = self.resolvedExportPath()
        dirname, filename = os.path.split(path)
        root, ext = os.path.splitext(filename)

        percentmatch = re.search('%\d+d', root)
        if percentmatch:
            percentpad = percentmatch.group()
            root = root.replace(percentpad, '')

        self._root = dirname + '/' + root.rstrip('#').rstrip('.')

        scriptExtension = '.nknc' if hiero.core.isNC() else '.nk'
        self._scriptfile = str(self._root + scriptExtension)

        # self.logger.info('TranscodeExporter writing script to %s', self._scriptfile)

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
            # ensure sub tasks do not create folders
            self._renderTask._makePath = FtrackProcessor._makePath(self)

    def updateItem(self, originalItem, localtime):
        self.createTranscodeScript()

    def _makePath(self):
        # disable making file paths
        FtrackProcessor._makePath(self)


class FtrackNukeRenderExporterPreset(TranscodePreset, FtrackProcessorPreset):
    def __init__(self, name, properties):
        TranscodePreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackNukeRenderExporter

        # Update preset with loaded data
        self.properties().update(properties)

    def set_ftrack_properties(self, properties):
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['asset_type_code'] = 'img'
        self.properties()['ftrack']['component_pattern'] = '.####.{ext}'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)

    def addUserResolveEntries(self, resolver):
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)


class FtrackNukeRenderExporterUI(TranscodeExporterUI, FtrackProcessorUI):
    def __init__(self, preset):
        TranscodeExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Nuke Render'
        self._taskType = FtrackNukeRenderExporter

    def populateUI(self, widget, exportTemplate):
        TranscodeExporterUI.populateUI(self, widget, exportTemplate)
        formLayout = FtrackProcessorUI.addFtrackTaskUI(self, widget, exportTemplate)

        # add reviewable component option
        key, value, label = 'opt_publish_review', True, 'Publish Review'
        review_tooltip = 'Generate and upload review'

        uiProperty = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ":",
            tooltip=review_tooltip
        )
        formLayout.addRow(label + ":", uiProperty)


hiero.core.taskRegistry.registerTask(FtrackNukeRenderExporterPreset, FtrackNukeRenderExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeRenderExporterPreset, FtrackNukeRenderExporterUI)
