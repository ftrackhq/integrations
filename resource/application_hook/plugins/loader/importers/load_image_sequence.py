# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline.asset import asset_info
from ftrack_connect_pipeline_nuke.constants import asset as asset_const
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class ImportNukePlugin(plugin.LoaderImporterNukePlugin):
    plugin_name = 'import_image_sequence'

    def run(self, context=None, data=None, options=None):
        #Add options import, open, reference
        results = {}
        paths_to_import = data
        for component_path in paths_to_import:
            self.logger.debug(
                'Loading image sequence {}'.format(component_path)
            )
            resulting_node = nuke.createNode('Read', inpanel=False)
            arguments_dict = asset_info.generate_asset_info_dict_from_args(
                context, data, options, self.session
            )
            asset_info_class = asset_info.FtrackAssetInfo(arguments_dict)
            unique_name = nuke_utils.get_unique_scene_name(
                '{}_{}'.format(
                    asset_info_class[asset_const.ASSET_NAME],
                    asset_info_class[asset_const.COMPONENT_NAME]
                )
            )
            resulting_node['name'].setValue(unique_name)
            resulting_node['file'].fromUserText(component_path)
            #Todo: Set start end frames from ftrack

            results[component_path] = resulting_node.name()

        return results


def register(api_object, **kw):
    plugin = ImportNukePlugin(api_object)
    plugin.register()