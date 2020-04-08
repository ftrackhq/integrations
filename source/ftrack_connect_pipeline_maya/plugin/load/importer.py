# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    BaseMayaPlugin, BaseMayaPluginWidget
)

import maya.cmds as cmd


class LoaderImporterMayaPlugin(plugin.LoaderImporterPlugin, BaseMayaPlugin):
    ''' Class representing a Collector Plugin

    .. note::

        _required_output a List
    '''

    def _run(self, event):
        self.old_data = set(cmd.ls())
        context = event['data']['settings']['context']
        data = event['data']['settings']['data']
        super_result = super(LoaderImporterMayaPlugin, self)._run(event)
        self.new_data = set(cmd.ls())

        asset_info = {}

        asset_info['asset_name'] = context.get('asset_name', 'No name found')
        asset_info['version_number'] = context.get('version_number', '0')
        asset_info['context_id'] = context.get('context_id', '')
        asset_info['asset_type'] = context.get('asset_type', '')
        asset_info['asset_id'] = context.get('asset_id', '')
        asset_info['version_id'] = context.get('version_id', '')

        asset_version = self.session.get('AssetVersion', asset_info['version_id'])

        location = self.session.pick_location()

        for component in asset_version['components']:
            if location.get_component_availability(component) == 0.0:
                continue
            component_path = location.get_filesystem_path(component)
            if component_path in data:
                asset_info['component_name'] = component['name']
                asset_info['component_id'] = component['id']
                asset_info['component_path'] = component_path

        if asset_info:
            self.linkToFtrackNode(asset_info)

        return super_result

    def linkToFtrackNode(self, asset_info):
        diff = self.new_data.difference(self.old_data)
        if not diff:
            self.logger.debug('No differences found in the scene')
            return

        ftrack_node_name = '{}_ftrackdata'.format(asset_info['asset_name'])
        count = 0
        while 1:
            if cmd.objExists(ftrack_node_name):
                ftrack_node_name = ftrack_node_name + str(count)
                count = count + 1
            else:
                break

        ftrack_node = cmd.createNode("ftrackAssetNode", name=ftrack_node_name)
        cmd.setAttr(
            '{}.assetVersion'.format(ftrack_node),
            int(asset_info['version_number'])
        )
        cmd.setAttr(
            '{}.assetId'.format(ftrack_node),
            asset_info['asset_id'], type="string"
        )
        cmd.setAttr(
            '{}.assetPath'.format(ftrack_node),
            asset_info['component_path'], type="string"
        )
        cmd.setAttr(
            '{}.assetTake'.format(ftrack_node),
            asset_info['component_name'], type="string"
        )
        cmd.setAttr(
            '{}.assetType'.format(ftrack_node),
            asset_info['asset_type'], type="string"
        )
        cmd.setAttr(
            '{}.assetComponentId'.format(ftrack_node),
            asset_info['component_id'],
            type="string"
        )

        for item in diff:
            if cmd.lockNode(item, q=True)[0]:
                cmd.lockNode(item, l=False)

            if not cmd.attributeQuery('ftrack', n=item, exists=True):
                cmd.addAttr(item, ln="ftrack", at="message")

            if not cmd.listConnections('{}.ftrack'.format(item)):
                cmd.connectAttr(
                    '{}.assetLink'.format(ftrack_node),
                    '{}.ftrack'.format(item)
                )


class ImporterMayaWidget(pluginWidget.LoaderImporterWidget, BaseMayaPluginWidget):
    ''' Class representing a Collector Widget

    .. note::

        _required_output a List
    '''

