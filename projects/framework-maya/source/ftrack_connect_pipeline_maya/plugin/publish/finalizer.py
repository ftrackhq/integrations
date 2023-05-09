# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    MayaBasePlugin,
    MayaBasePluginWidget,
)

import maya.cmds as cmds
from ftrack_connect_pipeline_maya import utils as maya_utils
from ftrack_connect_pipeline_maya.constants import asset as asset_const


class MayaPublisherFinalizerPlugin(
    plugin.PublisherFinalizerPlugin, MayaBasePlugin
):
    '''Class representing a Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''

    def _run(self, event):
        '''Run the current plugin with the settings form the *event*.

        .. note::

           We are not committing the changes here to ftrack, as they should be
           committed in the finalizer plugin itself. This way we avoid
           publishing the dependencies if the plugin fails.
        '''
        self.version_dependencies = []
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        for dependency in ftrack_asset_nodes:
            dependency_version_id = cmds.getAttr(
                '{}.{}'.format(dependency, asset_const.VERSION_ID)
            )
            self.logger.debug(
                'Adding dependency_asset_version_id: {}'.format(
                    dependency_version_id
                )
            )
            if dependency_version_id:

                dependency_version = self.session.query(
                    'select version from AssetVersion where id is "{}"'.format(
                        dependency_version_id
                    )
                ).one()

                if dependency_version not in self.version_dependencies:
                    self.version_dependencies.append(dependency_version)

        super_result = super(MayaPublisherFinalizerPlugin, self)._run(event)

        return super_result


class MayaPublisherFinalizerPluginWidget(
    pluginWidget.PublisherFinalizerPluginWidget, MayaBasePluginWidget
):
    '''Class representing a Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
