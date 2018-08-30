# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
import nuke
import hiero.core.util
from hiero.exporters.FnNukeShotExporter import NukeShotExporter, NukeShotPreset
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI

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

        self._plate_tag = None
        for tag in track_item_tags:
            if tag.name() == 'ftrack.Plate':
                self._plate_tag = tag
                break

        if not self._plate_tag :
            # if the plate tag is not existing we cannot reference the plate.
            self._nothingToDo = True

    def _beforeNukeScriptWrite(self, script):
        nodes = script.getNodes()
        for node in nodes:
            self.logger.info('Node: {}'.format(node.type()))
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

    def populateUI(self, widget, exportTemplate):
        # disable ui
        return


hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
