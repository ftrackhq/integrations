# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import os
import json

import unreal

import ftrack_connect_pipeline_unreal.constants as unreal_constants
from ftrack_connect_pipeline_unreal.constants import asset as asset_const

logger = logging.getLogger(__name__)


def get_ftrack_nodes():
    '''Returns all the ftrack nodes in the scene'''
    ftrack_nodes = []
    if not os.path.exists(unreal_constants.FTRACK_ROOT_PATH):
        return ftrack_nodes
    content = os.listdir(unreal_constants.FTRACK_ROOT_PATH)
    for item_name in content:
        if 'ftrackdata' not in item_name:
            continue
        if item_name.endswith(".json"):
            ftrack_nodes.append(os.path.splitext(item_name)[0])
    return ftrack_nodes  # str ["xxxx_ftrackdata_3642"] == list of node names


def get_current_scene_objects():
    '''Returns all the objects in the scene'''
    # Return the list of all the assets found in the DirectoryPath.
    # https://docs.unrealengine.com/5.1/en-US/PythonAPI/class/EditorAssetLibrary.html?highlight=editorassetlibrary#unreal.EditorAssetLibrary
    return set(
        unreal.EditorAssetLibrary.list_assets(
            unreal_constants.GAME_ROOT_PATH, recursive=True
        )
    )


def connect_object(node_name, asset_info, supplied_logger=None):
    '''Store metadata and save the Unreal asset given by *node_name*, based on *asset_info*'''

    from ftrack_connect_pipeline_unreal.utils import get_asset_by_path

    asset = get_asset_by_path(node_name)
    unreal.EditorAssetLibrary.set_metadata_tag(
        asset,
        asset_const.NODE_METADATA_TAG,
        str(asset_info.get(asset_const.ASSET_INFO_ID)),
    )

    # Have Unreal save the asset as it has been modified
    logger_effective = supplied_logger or logger
    logger_effective.debug('Saving asset: {}'.format(node_name))
    unreal.EditorAssetLibrary.save_asset(node_name)


def node_exists(node_name):
    '''Check if node_name exist in the project'''
    for content in unreal.EditorAssetLibrary.list_assets(
        unreal_constants.GAME_ROOT_PATH, recursive=True
    ):
        if node_name in content:
            return True
    return False


def ftrack_node_exists(dcc_object_name):
    '''Check if ftrack node identified by *node_name* exist in the project'''
    dcc_object_node = None
    ftrack_nodes = get_ftrack_nodes()
    for node in ftrack_nodes:
        if node == dcc_object_name:
            dcc_object_node = node
            break
    return dcc_object_node is not None


def rename_node_with_prefix(node_name, prefix):
    '''This method allow renaming a UObject to put a prefix to work along
    with UE4 naming convention.
      https://github.com/Allar/ue4-style-guide'''

    from ftrack_connect_pipeline_unreal.utils.asset import (
        asset_path_to_filesystem_path,
    )

    assert node_name is not None, 'No node name/asset path provided'
    object_ad = unreal.EditorAssetLibrary.find_asset_data(node_name)
    new_name_with_prefix = '{}/{}{}'.format(
        str(object_ad.package_path),
        prefix,
        str(object_ad.asset_name),
    )

    if unreal.EditorAssetLibrary.rename_asset(node_name, new_name_with_prefix):
        # Make sure previous files is deleted from disk, Unreal have a behaviour to leave a stub asset
        previous_asset_path = asset_path_to_filesystem_path(
            node_name, throw_on_error=False
        )
        if previous_asset_path and os.path.exists(previous_asset_path):
            logger.warning(
                'Removing previous asset file: {}'.format(previous_asset_path)
            )
            os.remove(previous_asset_path)
        return new_name_with_prefix
    else:
        return node_name


def rename_node_with_suffix(node_name, suffix):
    '''Rename asset *node_name* with *suffix*'''

    from ftrack_connect_pipeline_unreal.utils.asset import (
        asset_path_to_filesystem_path,
    )

    assert node_name is not None, 'No node name/asset path provided'
    object_ad = unreal.EditorAssetLibrary.find_asset_data(node_name)
    new_name_with_suffix = '{}/{}{}'.format(
        str(object_ad.package_path), str(object_ad.asset_name), suffix
    )

    if unreal.EditorAssetLibrary.rename_asset(node_name, new_name_with_suffix):
        # Make sure previous files is deleted from disk, Unreal have a behaviour to leave a stub asset
        previous_asset_path = asset_path_to_filesystem_path(
            node_name, throw_on_error=False
        )
        if previous_asset_path and os.path.exists(previous_asset_path):
            logger.warning(
                'Removing previous asset file: {}'.format(previous_asset_path)
            )
            os.remove(previous_asset_path)
        return new_name_with_suffix
    else:
        return node_name


def get_connected_nodes_from_dcc_object(dcc_object_name):
    '''Return all objects connected to the given *dcc_object_name*'''

    from ftrack_connect_pipeline_unreal.utils import get_asset_by_path

    objects = []
    dcc_object_node = None
    ftrack_nodes = get_ftrack_nodes()
    for node in ftrack_nodes:
        if node == dcc_object_name:
            dcc_object_node = node
            break
    if not dcc_object_node:
        return
    path_dcc_object_node = '{}{}{}.json'.format(
        unreal_constants.FTRACK_ROOT_PATH, os.sep, dcc_object_node
    )
    with open(
        path_dcc_object_node,
        'r',
    ) as openfile:
        param_dict = json.load(openfile)
    id_value = param_dict.get(asset_const.ASSET_INFO_ID)
    for node_name in get_current_scene_objects():
        asset = get_asset_by_path(node_name)
        for metadata_tag in [asset_const.NODE_METADATA_TAG]:
            ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
                asset, metadata_tag
            )
            if id_value == ftrack_value:
                objects.append(node_name)
    return objects


def delete_node(node_name):
    '''Delete the given *node_name*'''
    return unreal.EditorAssetLibrary.delete_asset(node_name)


def delete_ftrack_node(dcc_object_name):
    dcc_object_node = None
    ftrack_nodes = get_ftrack_nodes()
    for node in ftrack_nodes:
        if node == dcc_object_name:
            dcc_object_node = node
            break
    if not dcc_object_node:
        return False
    path_dcc_object_node = '{}{}{}.json'.format(
        unreal_constants.FTRACK_ROOT_PATH, os.sep, dcc_object_node
    )
    if os.path.exists(path_dcc_object_node):
        return os.remove(path_dcc_object_node)
    return False
