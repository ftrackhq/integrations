# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils

class PublisherFinaliserMaxPlugin(plugin.PublisherFinaliserPlugin, BaseMaxPlugin):
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
        context = event['data']['settings']['context']
        current_asset_id = context.get('asset_id', '')

        self.logger.info('context --> {}'.format(context))
        self.logger.info('current_version_id --> {}'.format(current_asset_id))

        self.version_dependencies = []
        ftrack_asset_nodes =max_utils.get_ftrack_helpers()

        for dependency in ftrack_asset_nodes:
            obj = dependency.Object
            dependency_asset_version_id = obj.ParameterBlock.assetVersionId.Value
            dependency_asset_id = obj.ParameterBlock.assetId.Value
            self.logger.info(
                'dependency_asset_id --> {}'.format(dependency_asset_version_id))
            if dependency_asset_version_id and dependency_asset_id != current_asset_id:
                dependency_version = self.session.get(
                    'AssetVersion', dependency_asset_version_id
                )
                if dependency_version not in self.version_dependencies:
                    self.version_dependencies.append(dependency_version)

        super_result = super(PublisherFinaliserMaxPlugin, self)._run(event)

        return super_result

class PublisherFinaliserMaxWidget(
    pluginWidget.PublisherFinaliserWidget, BaseMaxPluginWidget
):
    ''' Class representing a Finaliser Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
