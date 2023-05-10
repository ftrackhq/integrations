# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import json
from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_qt import plugin as pluginWidget

from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)

from ftrack_connect_pipeline_unreal import utils as unreal_utils
import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.constants import asset as asset_const


class UnrealPublisherFinalizerPlugin(
    plugin.PublisherFinalizerPlugin, UnrealBasePlugin
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
        ftrack_asset_nodes = unreal_utils.get_ftrack_nodes()
        for dcc_object_node_name in ftrack_asset_nodes:
            ftrack_file_path = os.path.join(
                unreal_constants.FTRACK_ROOT_PATH,
                "{}.json".format(dcc_object_node_name),
            )
            with open(ftrack_file_path, 'r') as openfile:
                param_dict = json.load(openfile)
            dependency_version_id = param_dict.get(asset_const.VERSION_ID)
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

        super_result = super(UnrealPublisherFinalizerPlugin, self)._run(event)

        return super_result


class UnrealPublisherFinalizerPluginWidget(
    pluginWidget.PublisherFinalizerPluginWidget, UnrealBasePluginWidget
):
    '''Class representing a Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
