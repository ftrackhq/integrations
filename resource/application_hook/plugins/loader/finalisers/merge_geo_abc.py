# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import re

import maya.cmds as cmd

from ftrack_connect_pipeline_maya import plugin
import ftrack_api


class MergeGeoAbcMayaPlugin(plugin.LoaderFinaliserMayaPlugin):
    plugin_name = 'merge_geo_abc'

    def run(self, context=None, data=None, options=None):
        result = {}
        asset_name = context.get('asset_name', '')
        ftrack_node_name = '{}_ftrackdata'.format(asset_name)
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
                if re.match(r'{}\d+'.format(maya_obj[0:-1]), alembic_maya_obj):
                    cmd.connectAttr(
                        r'{}.transOp[0]'.format(alembic_node),
                        r'{}.translateX'.format(maya_obj)
                    )
                    cmd.connectAttr(
                        r'{}.transOp[1]'.format(alembic_node),
                        r'{}.translateY'.format(maya_obj)
                    )
                    cmd.connectAttr(
                        r'{}.transOp[2]'.format(alembic_node),
                        r'{}.translateZ'.format(maya_obj)
                    )
                    result[maya_obj] = alembic_node
                    cmd.delete(alembic_maya_obj)

        return result


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MergeGeoAbcMayaPlugin(api_object)
    plugin.register()