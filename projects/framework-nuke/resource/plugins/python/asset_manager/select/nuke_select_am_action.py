# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import nuke

import ftrack_api

from ftrack_framework_core import plugin
from ftrack_framework_core import constants as core_constants

from ftrack_framework_nuke.constants import asset as asset_const
from ftrack_framework_nuke import utils as nuke_utils
from ftrack_framework_nuke.asset import NukeFtrackObjectManager
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


class NukeSelectAssetManagerActionPlugin(plugin.AssetManagerActionPlugin):
    plugin_name = 'nuke_select_am_action'

    FtrackObjectManager = NukeFtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = NukeDccObject
    '''DccObject class to use'''

    def run(self, context_data=None, data=None, options=None):
        '''Select all the Nuke assets provided in *data*'''

        result = []

        if options.get('clear_selection'):
            nuke_utils.clean_selection()

        for asset_info in data:
            import nuke

            nuke.tprint('@@@ asset_info: {}'.format(asset_info))

            dcc_object = self.DccObject(
                from_id=asset_info[asset_const.ASSET_INFO_ID]
            )

            nuke.tprint('@@@ dcc_object: {}'.format(dcc_object))

            self.dcc_object = dcc_object

            ftrack_node = nuke.toNode(self.dcc_object.name)

            parented_nodes = ftrack_node.getNodes()
            parented_nodes_names = [
                x.knob('name').value() for x in parented_nodes
            ]
            nodes_to_select_str = ftrack_node.knob(
                asset_const.ASSET_LINK
            ).value()
            nodes_to_select = parented_nodes_names
            if len(nodes_to_select_str) > 0:
                nodes_to_select = set(
                    nodes_to_select + nodes_to_select_str.split(";")
                )

            for node_name in nodes_to_select:
                try:
                    node_to_select = nuke.toNode(node_name)
                    node_to_select['selected'].setValue(True)
                    result.append(str(node_name))
                except Exception as error:
                    message = str(
                        'Could not select the node {}, error: {}'.format(
                            str(node_name), error
                        )
                    )
                    self.logger.error(message)
                    return False, {"message": message}

            try:
                ftrack_node['selected'].setValue(True)
                result.append(str(ftrack_node))
            except Exception as error:
                message = 'Could not select the dcc_object, error: {}'.format(
                    error
                )
                self.logger.error(message)
                return False, {"message": message}

        return result


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeSelectAssetManagerActionPlugin(api_object)
    plugin.register()
