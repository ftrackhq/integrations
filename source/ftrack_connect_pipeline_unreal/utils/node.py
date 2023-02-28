# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import os
import json

import unreal

from ftrack_connect_pipeline_unreal.constants import asset as asset_const

logger = logging.getLogger(__name__)


def get_ftrack_nodes():
    '''Returns all the ftrack nodes in the scene'''
    ftrack_nodes = []
    if not os.path.exists(asset_const.FTRACK_ROOT_PATH):
        return ftrack_nodes
    content = os.listdir(asset_const.FTRACK_ROOT_PATH)
    for item_name in content:
        if not "ftrackdata" in item_name:
            continue
        if item_name.endswith(".json"):
            ftrack_nodes.append(os.path.splitext(item_name)[0])
    return ftrack_nodes  # str ["xxxx_ftrackdata_3642"] == list of node names


def get_current_scene_objects():
    '''Returns all the objects in the scene'''
    # Return the list of all the assets found in the DirectoryPath.
    # https://docs.unrealengine.com/5.1/en-US/PythonAPI/class/EditorAssetLibrary.html?highlight=editorassetlibrary#unreal.EditorAssetLibrary
    return set(unreal.EditorAssetLibrary.list_assets("/Game", recursive=True))


def get_asset_info(node_name, snapshot=False):
    '''Return the asset info from dcc object linked to asset path identified by *node_name*'''

    from ftrack_connect_pipeline_unreal import utils as unreal_utils

    asset = unreal_utils.get_asset_by_path(node_name)
    if asset is None:
        logger.warning(
            '(get_asset_info) Cannot find asset by path: {}'.format(node_name)
        )
        return None, None
    ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
        asset, asset_const.NODE_METADATA_TAG
    )

    for dcc_object_node in get_ftrack_nodes():
        path_dcc_object_node = '{}{}{}.json'.format(
            asset_const.FTRACK_ROOT_PATH, os.sep, dcc_object_node
        )
        with open(
            path_dcc_object_node,
            'r',
        ) as openfile:
            param_dict = json.load(openfile)
        id_value = param_dict.get(asset_const.ASSET_INFO_ID)
        if id_value == ftrack_value:
            return dcc_object_node, param_dict
    return None, None


def connect_object(node_name, asset_info, logger):
    '''Store metadata and save the Unreal asset given by *node_name*, based on *asset_info*'''

    from ftrack_connect_pipeline_unreal import utils as unreal_utils

    asset = unreal_utils.get_asset_by_path(node_name)
    unreal.EditorAssetLibrary.set_metadata_tag(
        asset,
        asset_const.NODE_METADATA_TAG,
        str(asset_info.get(asset_const.ASSET_INFO_ID)),
    )

    # Have Unreal save the asset as it has been modified
    logger.debug('Saving asset: {}'.format(node_name))
    unreal.EditorAssetLibrary.save_asset(node_name)


def rename_node_with_prefix(node_name, prefix):
    '''This method allow renaming a UObject to put a prefix to work along
    with UE4 naming convention.
      https://github.com/Allar/ue4-style-guide'''
    assert node_name is not None, 'No node name/asset path provided'
    object_ad = unreal.EditorAssetLibrary.find_asset_data(node_name)
    new_name_with_prefix = '{}/{}{}'.format(
        str(object_ad.package_path),
        prefix,
        str(object_ad.asset_name),
    )

    if unreal.EditorAssetLibrary.rename_asset(node_name, new_name_with_prefix):
        return new_name_with_prefix
    else:
        return node_name
