# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_3dsmax.plugin import (
    BaseMaxPlugin, BaseMaxPluginWidget
)
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils


class PublisherFinalizerMaxPlugin(plugin.PublisherFinalizerPlugin, BaseMaxPlugin):
    ''' Class representing a Finalizer Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
            current asset
    '''

    def _run(self, event):
        ''' Run the current plugin with the settings form the *event*.

            .. note::

               We are not committing the changes here to ftrack, as they should be
               committed in the finalizer plugin itself. This way we avoid
               publishing the dependencies if the plugin fails.
        '''
        self.version_dependencies = []
        ftrack_asset_nodes =max_utils.get_ftrack_helpers()

        for dependency in ftrack_asset_nodes:
            obj = dependency
            dependency_version_id = obj.version_id
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

        super_result = super(PublisherFinalizerMaxPlugin, self)._run(event)

        return super_result

class PublisherFinalizerMaxWidget(
    pluginWidget.PublisherFinalizerWidget, BaseMaxPluginWidget
):
    ''' Class representing a Finalizer Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
            current asset
    '''
