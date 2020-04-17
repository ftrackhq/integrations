# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import os

import hiero.core.util
from hiero.exporters.FnCopyExporter import CopyExporter, CopyPreset
from hiero.exporters.FnCopyExporterUI import CopyExporterUI
from hiero.exporters.FnShotExporter import ShotTask

from ftrack_connect_nuke_studio.config import report_exception
from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset, FtrackProcessor,
)


class FtrackCopyExporter(CopyExporter, FtrackProcessor):

    @report_exception
    def __init__(self, init_dict):
        super(FtrackCopyExporter, self).__init__(init_dict)
        FtrackProcessor.__init__(self, init_dict)

    def _makePath(self):
        pass

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def startTask(self):
        # 'CopyExporter' parent 'FrameExporter' overrides the 'startTask' method,
        # and TaskCallbacks registered in FtrackProcesser are not called,
        # so bypasses the parent class and calls ShotTask 'startTask' method directly.
        ShotTask.startTask(self)

        # Fix CopyExporter defaults to using data from 'self._paths'
        # instead of data source used in 'FtrackProcessor.setup_export_paths_event' callback.
        if self._source.singleFile():
            if self._currentPathIndex < len(self._paths):
                src_path, _ = self._paths[self._currentPathIndex]
                self._paths[self._currentPathIndex] = (src_path, self._exportPath)
        else:
            for index, (src_path, _) in enumerate(self._paths):
                dst_path = '{root_path}/{name}.{frame}.{ext}'.format(
                    root_path=os.path.dirname(self._exportPath),
                    name=self.component_name(),
                    frame='{}'.format(self.filepadding()) % index,
                    ext=self.fileext()
                )
                self._paths[index] = (src_path, dst_path)


class FtrackCopyExporterPreset(CopyPreset, FtrackProcessorPreset):

    @report_exception
    def __init__(self, name, properties):
        super(FtrackCopyExporterPreset, self).__init__(name, properties)
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
        self.properties()['ftrack']['component_pattern'] = '.####.{ext}'
        self.properties()['ftrack']['component_name'] = 'Plate'
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


class FtrackCopyExporterUI(CopyExporterUI):

    def __init__(self, preset):
        super(FtrackCopyExporterUI, self).__init__(preset)
        self._displayName = 'Ftrack Copy Exporter'


hiero.core.taskRegistry.registerTask(FtrackCopyExporterPreset, FtrackCopyExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackCopyExporterPreset, FtrackCopyExporterUI)
