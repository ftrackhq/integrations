# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as fcc
from ftrack_connect_pipeline_3dsmax.utils import ftrack_asset_node


class LoaderImporterMaxPlugin(plugin.LoaderImporterPlugin, BaseMaxPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    def _run(self, event):
        self.old_data = fcc.get_current_scene_objects()
        self.logger.debug('Got current objects from scene')

        context = event['data']['settings']['context']
        self.logger.debug('Current context : {}'.format(context))

        data = event['data']['settings']['data']
        self.logger.debug('Current data : {}'.format(data))

        self.logger.debug('Running the base _run function')
        super_result = super(LoaderImporterMaxPlugin, self)._run(event)
        self.logger.debug('Base _run function done.')

        self.new_data = fcc.get_current_scene_objects()
        self.logger.debug(
            'Got all the objects in the scene after import'
        )

        self.logger.debug('Building asset_info dictionary')
        asset_info = {}

        asset_info['asset_name'] = context.get('asset_name', 'No name found')
        asset_info['version_number'] = context.get('version_number', '0')
        asset_info['context_id'] = context.get('context_id', '')
        asset_info['asset_type'] = context.get('asset_type', '')
        asset_info['asset_id'] = context.get('asset_id', '')
        asset_info['version_id'] = context.get('version_id', '')

        asset_version = self.session.get(
            'AssetVersion', asset_info['version_id']
        )

        location = self.session.pick_location()

        for component in asset_version['components']:
            if location.get_component_availability(component) < 100.0:
                continue
            component_path = location.get_filesystem_path(component)
            if component_path in data:
                asset_info['component_name'] = component['name']
                asset_info['component_id'] = component['id']
                asset_info['component_path'] = component_path

        if asset_info:
            self.logger.debug(
                'asset_info dictionary done : {}'.format(asset_info)
            )
            self.link_to_ftrack_node(asset_info)

        return super_result

    def link_to_ftrack_node(self, asset_info):
        diff = self.new_data.difference(self.old_data)

        if not diff:
            self.logger.debug('No differences found in the scene')
            return

        self.logger.debug(
            'Checked differences between nodes before and after'
            ' inport : {}'.format(diff)
        )

        #TODO: asset_import_mode has to come from the ui
        ftrack_node_class = ftrack_asset_node.FtrackAssetNode(
            asset_info, asset_import_mode="import"
        )
        ftrack_node = ftrack_node_class.create_node()

        for item in diff:
            ftrack_node_class.connect_to_ftrack_node(item)
            self.logger.debug(
                'item {} added to ftrack node {}'.format(item, ftrack_node)
            )


class ImporterMaxWidget(pluginWidget.LoaderImporterWidget, BaseMaxPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

