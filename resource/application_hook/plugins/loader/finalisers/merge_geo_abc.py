# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin


class MergeGeoAbcMayaPlugin(plugin.FinaliserMayaPlugin):
    plugin_name = 'merge_geo_abc'

    def run(self, context=None, data=None, options=None):
        result = {}
        asset_name = context.get('asset_name', '')
        ftrack_node_name = asset_name + "_ftrackdata"
        ftrack_nodes = cmd.ls(ftrack_node_name, type='ftrackAssetNode')
        alembic_nodes = cmd.ls(type='AlembicNode')

        maya_objects = []
        for obj in ftrack_nodes:
            assetLink = cmd.listConnections(obj, et=True, type='transform')
            maya_objects.extend(assetLink)

        for alembic_node in alembic_nodes:
            alembic_maya_obj = cmd.listConnections(
                alembic_node, et=True, type='transform'
            )[0]
            for maya_obj in maya_objects:
                if maya_obj.endsWith(alembic_maya_obj):
                    cmd.connectAttr(alembic_node + '.transOp',
                                     maya_obj + '.translate')
                    result[maya_obj] = alembic_node
                    cmd.delete(alembic_maya_obj)

        return result


def register(api_object, **kw):
    plugin = MergeGeoAbcMayaPlugin(api_object)
    plugin.register()