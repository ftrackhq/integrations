# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero.core.util
from hiero.exporters.FnNukeShotExporter import NukeShotExporter, NukeShotPreset
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI
from hiero.exporters.FnTranscodeExporter import TranscodePreset
from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory

from ftrack_connect_nuke_studio.config import report_exception

from ftrack_connect_nuke_studio.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackNukeShotExporter(NukeShotExporter, FtrackProcessor):
    '''Shot Task exporter.'''

    @report_exception
    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        NukeShotExporter.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)
        self._source_tag = None

    def component_name(self):
        return self.sanitise_for_filesystem(
            self._resolver.resolve(self, self._preset.name())
        )

    def _beforeNukeScriptWrite(self, script):
        '''Call-back method introduced to allow modifications of the script
        object before it is written to disk.
        '''
        track_item = self._init_dict.get('item')
        task_label = self._preset.properties()['ftrack']['reference_task']
        ftrack_tags = [
            tag for tag in track_item.tags() if (
                tag.metadata().hasKey('tag.provider') and tag.metadata()['tag.provider'] == 'ftrack'
            )
        ]

        for tag in ftrack_tags:
            if tag.name() == task_label:
                self._source_tag = tag
                break

        if not self._source_tag:
            # If the plate tag is not existing we cannot reference the plate.
            self._nothingToDo = True

        nodes = script.getNodes()
        for node in nodes:
            if node.type() == 'Read' and self._source_tag:
                tag_metadata = self._source_tag.metadata()
                component_id = tag_metadata['tag.component_id']
                ftrack_component = self.session.get('Component', component_id)
                ftrack_component_name = ftrack_component['name']
                ftrack_version_id = ftrack_component['version']['id']
                ftrack_version = ftrack_component['version']['version']
                ftrack_asset = ftrack_component['version']['asset']
                ftrack_asset_name = ftrack_asset['name']
                ftrack_asset_type = ftrack_asset['type']['short']

                node.addTabKnob('ftracktab', 'ftrack')
                node.addInputTextKnob('componentId', 'componentId', value=component_id)
                node.addInputTextKnob('componentName', 'componentName', value=ftrack_component_name)
                node.addInputTextKnob('assetVersionId', 'assetVersionId', value=ftrack_version_id)
                node.addInputTextKnob('assetVersion', 'assetVersion', value=ftrack_version)
                node.addInputTextKnob('assetName', 'assetName', value=ftrack_asset_name)
                node.addInputTextKnob('assetType', 'assetType', value=ftrack_asset_type)

    def _makePath(self):
        '''Disable file path creation.'''
        pass


class FtrackNukeShotExporterPreset(NukeShotPreset, FtrackProcessorPreset):
    '''Shot Task preset.'''

    @report_exception
    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        '''Initialise task with *name* and *properties*.'''
        NukeShotPreset.__init__(self, name, properties, task)
        FtrackProcessorPreset.__init__(self, name, properties)
        # Update preset with loaded data
        self.properties().update(properties)
        self.setName(self.properties()['ftrack']['component_name'])

        # Ensure to nullify read and write paths by default
        # to ensure duplication of task.
        self.properties()['readPaths'] = ['']
        self.properties()['writePaths'] = ['']
        self.properties()['timelineWriteNode'] = ''

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
        self.properties()['ftrack']['component_name'] = 'NukeScript'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)
        self.properties()['ftrack']['reference_task'] = None

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


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackProcessorUI):
    '''Shot Task Ui.'''

    @report_exception
    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''

        NukeShotExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Nuke File'
        self._taskType = FtrackNukeShotExporter

    def addTaskSelector(self, parent_layout, exportTemplate):
        '''Provide widget praented to *layout* to select
        from available instanciated tasks from *exportTemplate*.
        '''
        available_tasks_names = [
            preset.name() for path, preset in exportTemplate.flatten() if (
                isinstance(preset, TranscodePreset)
            )
        ]

        key, value, label = 'reference_task', available_tasks_names, 'Source component'
        tooltip = 'Select component output as input for nuke script read node.'

        available_tasks_options = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=tooltip
        )
        parent_layout.addRow(label + ':', available_tasks_options)
        available_tasks_options.update(True)

    def populateUI(self, widget, exportTemplate):
        '''PopulateUIExport dialog to allow the TaskUI to populate
        a QWidget with the ui *widget* neccessary to reflect the current preset.
        '''
        NukeShotExporterUI.populateUI(self, widget, exportTemplate)

        form_layout = TaskUIFormLayout()
        layout = widget.layout()
        layout.addLayout(form_layout)
        form_layout.addDivider('Ftrack Options')

        self.addFtrackTaskUI(form_layout, exportTemplate)
        self.addTaskSelector(form_layout, exportTemplate)

        self._nodeSelectionWidget.setHidden(True)
        self._timelineWriteNode.setHidden(True)


hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
