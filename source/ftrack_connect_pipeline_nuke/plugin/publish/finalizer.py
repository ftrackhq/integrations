# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os
import re
import clique

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class NukePublisherFinalizerPlugin(
    plugin.PublisherFinalizerPlugin, NukeBasePlugin
):
    '''Class representing a Finalizer Plugin

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''

    def _run(self, event):
        self.version_dependencies = []
        ftrack_asset_nodes = nuke_utils.get_nodes_with_ftrack_tab()

        for dependency in ftrack_asset_nodes:
            # avoid read and write nodes containing the old ftrack tab
            # without information
            if not dependency.knob(asset_const.VERSION_ID):
                break
            dependency_version_id = dependency.knob(
                asset_const.VERSION_ID
            ).getValue()
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

        super_result = super(NukePublisherFinalizerPlugin, self)._run(event)

        data = event['data']['settings']['data']

        cleanup_files = []
        for step in data:
            if step['type'] == constants.COMPONENT:
                component_name = step['name']
                for stage in step['result']:
                    for plugin in stage['result']:
                        for component_path in plugin['result']:
                            if re.search(
                                '(?<=\.)((%+\d+d)|(#+)|(%d)|(\d+))(?=\.)',
                                component_path,
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


class NukePublisherFinalizerPluginWidget(
    pluginWidget.PublisherFinalizerPluginWidget, NukeBasePluginWidget
):
    '''Class representing a Finalizer Widget

    .. note::

        _required_output is a dictionary containing the 'context_id',
        'asset_name', 'asset_type_name', 'comment' and 'status_id' of the
        current asset
    '''
