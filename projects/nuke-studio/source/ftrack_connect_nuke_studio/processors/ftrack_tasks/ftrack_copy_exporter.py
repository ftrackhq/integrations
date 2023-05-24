# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import os

import hiero.core.util
from hiero.exporters.FnCopyExporter import CopyExporter, CopyPreset
from hiero.exporters.FnCopyExporterUI import CopyExporterUI
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.core.FnExporterBase import TaskCallbacks

from ftrack_connect_nuke_studio.config import report_exception

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackCopyExporter(CopyExporter, FtrackProcessor):

    @report_exception
    def __init__(self, init_dict):
        CopyExporter.__init__(self, init_dict)
        FtrackProcessor.__init__(self, init_dict)

    def _makePath(self):
        pass

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def finishTask(self):
        TaskCallbacks.call(TaskCallbacks.onTaskFinish, self)
        CopyExporter.finishTask(self)

    def startTask(self):
        '''Override startTask.'''
        TaskCallbacks.call(TaskCallbacks.onTaskStart, self)
        CopyExporter.startTask(self)

    @report_exception
    def doFrame(self, src, dst):
        '''Override per frame function to allow a proper registration 
            into ftrack.
        
        '''
        if not self._source.singleFile():
            dst_path = os.path.dirname(self._exportPath)
            dst_file_tokens = os.path.basename(dst).split('.')[-2:]
            dst_tokens = [self.component_name().lower()]
            dst_tokens.extend(dst_file_tokens)
            dst_name = '{0}.{1}.{2}'.format(
                *dst_tokens
            )

            dst = os.path.join(dst_path, dst_name)
        else:
            dst = self._exportPath

        # Copy file including the permission bits, last access time, last modification time, and flags
        self._tryCopy(src, dst)


class FtrackCopyExporterPreset(CopyPreset, FtrackProcessorPreset):

    @report_exception
    def __init__(self, name, properties):
        CopyPreset.__init__(self, name, properties)
        FtrackProcessorPreset.__init__(self, name, properties)
        self._parentType = FtrackCopyExporter

        # Update preset with loaded data
        self.properties().update(properties)
        self.setName(self.name())

    def name(self):
        return self.properties()['ftrack']['component_name']

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for task.'''
        super(FtrackCopyExporterPreset, self).set_ftrack_properties(properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # Add placeholders for default ftrack defaults
        # '####' this format can be used in sequence or single file.
        self.properties()['ftrack']['component_pattern'] = '.%d.{ext}'
        self.properties()['ftrack']['component_name'] = 'Ingest'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)

    def addUserResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''
        super(FtrackCopyExporterPreset, self).addFtrackResolveEntries(resolver)

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

        resolver.addResolver(
            "{ext}",
            "Extension of the file to be output",
            lambda keyword, task: task.fileext()
        )


class FtrackCopyExporterUI(CopyExporterUI, FtrackProcessorUI):

    def __init__(self, preset):
        CopyExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)
        self._displayName = 'Ftrack Copy Exporter'
        self._taskType = FtrackCopyExporter

    def populateUI(self, widget, exportTemplate):
        CopyExporterUI.populateUI(self, widget, exportTemplate)
        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Ftrack Options')

        self.addFtrackTaskUI(form_layout, exportTemplate)

hiero.core.taskRegistry.registerTask(FtrackCopyExporterPreset, FtrackCopyExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackCopyExporterPreset, FtrackCopyExporterUI)
