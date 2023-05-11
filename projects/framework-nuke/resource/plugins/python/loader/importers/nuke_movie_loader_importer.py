# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os
import traceback
import clique

import ftrack_api

import nuke

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.constants import asset as asset_const


class NukeRenderLoaderImporterPlugin(plugin.NukeLoaderImporterPlugin):
    '''Nuke render loader plugin'''

    plugin_name = 'nuke_movie_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load collected video file(s) supplied with *data* into Nuke'''

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:
            self.logger.debug('Loading render/movie {}'.format(component_path))
            resulting_node = nuke.createNode('Read', inpanel=False)
            resulting_node['file'].fromUserText(component_path)

            results[component_path] = resulting_node.name()

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeRenderLoaderImporterPlugin(api_object)
    plugin.register()
