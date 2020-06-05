# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os
import re
import clique

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

        cleanup_files = []
        for component_name, component_path in data.items():
            if re.search(
                    '(?<=\.)((%+\d+d)|(#+)|(%d)|(\d+))(?=\.)', component_path
            ):
                sequence_path = clique.parse(component_path)
                seq_paths = list(sequence_path)
                cleanup_files.extend(seq_paths)
            else:
                cleanup_files.append(component_path)
        for path in cleanup_files:
            if os.path.exists(path):
                os.remove(path)
                self.logger.debug('removing path {} '.format(path))

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
