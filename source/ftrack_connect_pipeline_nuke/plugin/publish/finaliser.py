# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    BaseNukePlugin, BaseNukePluginWidget
)
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils

class PublisherFinaliserNukePlugin(plugin.PublisherFinaliserPlugin, BaseNukePlugin):
    ''' Class representing a Finaliser Plugin

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''

    def _run(self, event):
        self.version_dependencies = []
        ftrack_asset_nodes = nuke_utils.get_nodes_with_ftrack_tab()

        for dependency in ftrack_asset_nodes:
            dependency_version_id = dependency.knob(
                asset_const.VERSION_ID).getValue()
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

        super_result = super(PublisherFinaliserNukePlugin, self)._run(event)

        data = event['data']['settings']['data']

        for component_name, component_path in data.items():
            if os.path.exists(component_path):
                os.remove(component_path)

        return super_result


class PublisherFinaliserNukeWidget(
    pluginWidget.PublisherFinaliserWidget, BaseNukePluginWidget
):
    ''' Class representing a Finaliser Widget

        .. note::

            _required_output is a dictionary containing the 'context_id',
            'asset_name', 'asset_type', 'comment' and 'status_id' of the
            current asset
    '''
