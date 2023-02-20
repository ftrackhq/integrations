# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os
import traceback
import clique

import ftrack_api

import nuke

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils
from ftrack_connect_pipeline_nuke.constants import asset as asset_const


class NukeSequenceLoaderImporterPlugin(plugin.NukeLoaderImporterPlugin):
    '''Nuke image sequence loader plugin'''

    plugin_name = 'nuke_sequence_loader_importer'

    def run(self, context_data=None, data=None, options=None):
        '''Load collected image sequence(s) supplied with *data* into Nuke'''

        results = {}

        paths_to_import = []
        for collector in data:
            paths_to_import.append(
                collector['result'].get(asset_const.COMPONENT_PATH)
            )

        for component_path in paths_to_import:
            self.logger.debug(
                'Loading image sequence {}'.format(component_path)
            )
            resulting_node = nuke.createNode('Read', inpanel=False)

            resulting_node['file'].fromUserText(component_path)
            # Detect frame range based on files on disk (safe)
            if component_path.find('%0') > 0:
                try:
                    directory, filename = os.path.split(component_path)
                    self.logger.debug(
                        'Calculating frame range from contents in: {}, sequence: {}'.format(
                            directory, filename
                        )
                    )
                    if os.path.exists(directory):
                        split_pos = filename.find('%')
                        prefix = filename[:split_pos]
                        suffix = filename[filename.find('d', split_pos) + 1 :]
                        files = []
                        for fn in sorted(os.listdir(directory)):
                            if fn.startswith(prefix) and fn.endswith(suffix):
                                files.append(fn)
                        collections = clique.assemble(files)[0]
                        range = collections[0].format('{range}')
                        read_first = int(range.split('-')[0])
                        read_last = int(range.split('-')[1])
                        resulting_node["first"].setValue(read_first)
                        resulting_node["last"].setValue(read_last)
                        resulting_node["origfirst"].setValue(read_first)
                        resulting_node["origlast"].setValue(read_last)
                except:
                    self.logger.warning(traceback.format_exc())

            results[component_path] = resulting_node.name()

        return results


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeSequenceLoaderImporterPlugin(api_object)
    plugin.register()
