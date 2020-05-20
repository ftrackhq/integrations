# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_maya.plugin import (
    BaseMayaPlugin, BaseMayaPluginWidget
)

import maya.cmds as cmd
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils
from ftrack_connect_pipeline.constants import asset as asset_const


class PublisherFinaliserMayaPlugin(plugin.PublisherFinaliserPlugin, BaseMayaPlugin):
    ''' Class representing a Finaliser Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''

    def _run(self, event):
        ''' Run the current plugin with the settings form the *event*.

            .. note::

               We are not committing the changes here to ftrack, as they should be
               committed in the finaliser plugin itself. This way we avoid
               publishing the dependencies if the plugin fails.
        '''
        self.version_dependencies = []
        ftrack_asset_nodes = maya_utils.get_ftrack_nodes()
        for dependency in ftrack_asset_nodes:
            dependency_version_id = cmd.getAttr('{}.{}'.format(
                dependency, asset_const.VERSION_ID
            ))
            self.logger.debug(
                'Adding dependency_asset_version_id: {}'.format(
                    dependency_version_id
                )
            )
            if dependency_version_id:
                dependency_version = self.session.get(
                    'AssetVersion', dependency_version_id
                )
                if dependency_version not in self.version_dependencies:
                    self.version_dependencies.append(dependency_version)

        super_result = super(PublisherFinaliserMayaPlugin, self)._run(event)

        return super_result

class PublisherFinaliserMayaWidget(
    pluginWidget.PublisherFinaliserWidget, BaseMayaPluginWidget
):
    ''' Class representing a Finaliser Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
