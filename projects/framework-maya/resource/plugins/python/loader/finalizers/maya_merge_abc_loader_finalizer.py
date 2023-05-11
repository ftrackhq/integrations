# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import re

import maya.cmds as cmds

from ftrack_connect_pipeline_maya import plugin
import ftrack_api


class MayaMergeAbcLoaderFinalizerPlugin(plugin.MayaLoaderFinalizerPlugin):
    '''Maya alembic loader finalizer plugin'''

    plugin_name = 'maya_merge_abc_loader_finalizer'

    def run(self, context_data=None, data=None, options=None):
        '''Merge Alembic nodes, identified by *context_data*'''
        result = {}
        asset_name = context_data.get('asset_name', '')
        ftrack_node_name = '{}_ftrackdata'.format(asset_name)
        ftrack_nodes = cmds.ls(ftrack_node_name, type='ftrackAssetNode')
        alembic_nodes = cmds.ls(type='AlembicNode')

        maya_objects = []
        for obj in ftrack_nodes:
            assetLink = cmds.listConnections(obj, et=True, type='transform')
            maya_objects.extend(assetLink)

        for alembic_node in alembic_nodes:
            alembic_maya_obj = cmds.listConnections(
                alembic_node, et=True, type='transform'
            )[0]
            for maya_obj in maya_objects:
                matchable_name = maya_obj.split(":")[-1]
                if re.match(
                    r'{}\d+'.format(matchable_name[0:-1]), alembic_maya_obj
                ):
                    cmds.connectAttr(
                        r'{}.transOp[0]'.format(alembic_node),
                        r'{}.translateX'.format(maya_obj),
                    )
                    cmds.connectAttr(
                        r'{}.transOp[1]'.format(alembic_node),
                        r'{}.translateY'.format(maya_obj),
                    )
                    cmds.connectAttr(
                        r'{}.transOp[2]'.format(alembic_node),
                        r'{}.translateZ'.format(maya_obj),
                    )
                    result[maya_obj] = alembic_node
                    cmds.delete(alembic_maya_obj)

        return result


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaMergeAbcLoaderFinalizerPlugin(api_object)
    plugin.register()
