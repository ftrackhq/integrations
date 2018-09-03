# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
import nuke
import hiero.core.util
from hiero.exporters.FnNukeShotExporter import NukeShotExporter, NukeShotPreset
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI

from hiero.ui.FnTaskUIFormLayout import TaskUIFormLayout
from hiero.ui.FnUIProperty import UIPropertyFactory

from QtExt import QtCore, QtWidgets, QtGui

from ftrack_connect_nuke_studio_beta.processors.ftrack_base.ftrack_base_processor import (
    FtrackProcessorPreset,
    FtrackProcessor,
    FtrackProcessorUI
)


class FtrackNukeShotExporter(NukeShotExporter, FtrackProcessor):
    '''Shot Task exporter.'''

    def __init__(self, initDict):
        '''Initialise task with *initDict*.'''
        NukeShotExporter.__init__(self, initDict)
        FtrackProcessor.__init__(self, initDict)
        track_item = self._init_dict.get('item')
        track_item_tags = track_item.tags()

        task_label = self._preset.properties()['ftrack']['reference_task']
        self.logger.info('Selected task: {}'.format(task_label))
        self._plate_tag = None
        for tag in track_item_tags:
            if tag.name() == 'ftrack.{}'.format(task_label):
                self._plate_tag = tag
                break

        self.logger.info('tag: {}'.format(self._plate_tag))

        if not self._plate_tag :
            # if the plate tag is not existing we cannot reference the plate.
            self._nothingToDo = True

    def _beforeNukeScriptWrite(self, script):
        ''' Call-back method introduced to allow modifications of the script object before it is written to disk.'''
        nodes = script.getNodes()
        for node in nodes:
            if node.type() == 'Read' and self._plate_tag:
                tag_metadata = self._plate_tag.metadata()
                component_id = tag_metadata['tag.component_id']
                ftrack_component = self.session.get('Component', component_id)
                ftrack_component_name = ftrack_component['name']
                ftrack_version_id = ftrack_component['version']['id']
                ftrack_version = ftrack_component['version']['version']
                ftrack_asset = ftrack_component['version']['asset']
                ftrack_asset_name = ftrack_asset['name']
                ftrack_asset_type = ftrack_asset['type']['short']

                node.addTabKnob("ftracktab", "ftrack")
                node.addInputTextKnob("componentId", "componentId", value=component_id)
                node.addInputTextKnob("componentName", "componentName", value=ftrack_component_name)
                node.addInputTextKnob("assetVersionId", "assetVersionId", value=ftrack_version_id)
                node.addInputTextKnob("assetVersion", "assetVersion", value=ftrack_version)
                node.addInputTextKnob("assetName", "assetName", value=ftrack_asset_name)
                node.addInputTextKnob("assetType", "assetType", value=ftrack_asset_type)

    def _makePath(self):
        '''Disable file path creation.'''
        pass


class FtrackNukeShotExporterPreset(NukeShotPreset, FtrackProcessorPreset):
    '''Shot Task preset.'''

    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        '''Initialise task with *name* and *properties*.'''
        NukeShotPreset.__init__(self, name, properties, task)
        FtrackProcessorPreset.__init__(self, name, properties)
        # Update preset with loaded data
        self.properties().update(properties)
        self.setName('NukeScript')

    def set_ftrack_properties(self, properties):
        '''Set ftrack specific *properties* for task.'''
        FtrackProcessorPreset.set_ftrack_properties(self, properties)
        properties = self.properties()
        properties.setdefault('ftrack', {})
        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['component_pattern'] = '.{ext}'
        self.properties()['ftrack']['task_id'] = hash(self.__class__.__name__)
        self.properties()['ftrack']['reference_task'] = None

    def addUserResolveEntries(self, resolver):
        '''Add ftrack resolve entries to *resolver*.'''
        FtrackProcessorPreset.addFtrackResolveEntries(self, resolver)


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackProcessorUI):
    '''Shot Task Ui.'''

    def __init__(self, preset):
        '''Initialise task ui with *preset*.'''

        NukeShotExporterUI.__init__(self, preset)
        FtrackProcessorUI.__init__(self, preset)

        self._displayName = 'Ftrack Nuke File'
        self._taskType = FtrackNukeShotExporter

    def addTaskSelector(self, layout, exportTemplate):
        formLayout = TaskUIFormLayout()
        layout.addLayout(formLayout)

        available_tasks_names = [preset.name() for path, preset in exportTemplate.flatten()]

        key, value, label = 'reference_task', available_tasks_names, 'Source Tasks'
        tooltip = 'Select task as input for nuke script read node.'

        self.available_tasks_options = UIPropertyFactory.create(
            type(value),
            key=key,
            value=value,
            dictionary=self._preset.properties()['ftrack'],
            label=label + ':',
            tooltip=tooltip
        )
        formLayout.addRow(label + ':', self.available_tasks_options)
        self.available_tasks_options.update(True)

    def populateUI(self, widget, exportTemplate):
        '''PopulateUIExport dialog to allow the TaskUI to populate a QWidget with the ui *widget*
        neccessary to reflect the current preset
        '''
        NukeShotExporterUI.populateUI(self, widget, exportTemplate)
        self.addTaskSelector(widget.layout(), exportTemplate)

        self._nodeSelectionWidget.setHidden(True)
        self._timelineWriteNode.setHidden(True)

hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
