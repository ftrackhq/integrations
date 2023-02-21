# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import os
import json

import unreal

from ftrack_connect_pipeline_unreal.constants import asset as asset_const


from ftrack_connect_pipeline_unreal.utils import (
    file as unreal_file_utils,
)

logger = logging.getLogger(__name__)

### NODE/OBJECT OPERATIONS ###


def get_ftrack_nodes():
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


def collect_children_nodes(node):
    '''Return all the children of the given *node*'''
    # child_nodes = []
    # for child in node.Children:
    #     _collect_children_nodes(child, child_nodes)
    #
    # return child_nodes
    pass


def _collect_children_nodes(n, nodes):
    '''Private function to recursively return children of the given *nodes*'''
    # for child in n.Children:
    #     _collect_children_nodes(child, nodes)
    #
    # nodes.append(n)
    pass


def delete_all_children(node):
    '''Delete all children from the given *node*'''
    # all_children = collect_children_nodes(node)
    # for node in all_children:
    #     rt.delete(node)
    # return all_children
    pass


def node_exists(node_name):
    '''Check if node_name exist in the project'''
    for content in unreal.EditorAssetLibrary.list_assets(
        "/Game", recursive=True
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


def get_asset_by_path(node_name):
    '''Get Unreal asset object by path'''
    if not node_name:
        return None
    assetRegistry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_data = assetRegistry.get_assets_by_package_name(
        os.path.splitext(node_name)[0]
    )
    if asset_data:
        return asset_data[0].get_asset()
    return None


def get_asset_by_class(class_name):
    return [
        asset
        for asset in unreal.AssetRegistryHelpers.get_asset_registry().get_all_assets()
        if asset.get_class().get_name() == class_name
    ]


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
        asset_const.FTRACK_ROOT_PATH, os.sep, dcc_object_node
    )
    if os.path.exists(path_dcc_object_node):
        return os.remove(path_dcc_object_node)
    return False


def get_connected_nodes_from_dcc_object(dcc_object_name):
    '''Return all objects connected to the given *dcc_object_name*'''
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
        asset_const.FTRACK_ROOT_PATH, os.sep, dcc_object_node
    )
    with open(
        path_dcc_object_node,
        'r',
    ) as openfile:
        param_dict = json.load(openfile)
    id_value = param_dict.get(asset_const.ASSET_INFO_ID)
    for node_name in get_current_scene_objects():
        asset = get_asset_by_path(node_name)
        for metadata_tag in [
            asset_const.NODE_METADATA_TAG,
            asset_const.NODE_SNAPSHOT_METADATA_TAG,
        ]:
            ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
                asset, metadata_tag
            )
            if id_value == ftrack_value:
                objects.append(node_name)
    return objects


def get_asset_info(node_name, snapshot=False):
    '''Return the asset info from dcc object linked to asset path identified by *node_name*'''

    asset = get_asset_by_path(node_name)
    if asset is None:
        logger.warning(
            '(get_asset_info) Cannot find asset by path: {}'.format(node_name)
        )
        return None, None
    ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
        asset,
        asset_const.NODE_METADATA_TAG
        if not snapshot
        else asset_const.NODE_SNAPSHOT_METADATA_TAG,
    )

    for dcc_object_node in get_ftrack_nodes():
        param_dict = read_asset_node(dcc_object_node)
        id_value = param_dict.get(asset_const.ASSET_INFO_ID)
        if id_value == ftrack_value:
            return dcc_object_node, param_dict
    return None, None


def read_asset_node(dcc_object_node):
    path_dcc_object_node = '{}{}{}.json'.format(
        asset_const.FTRACK_ROOT_PATH, os.sep, dcc_object_node
    )
    if os.path.exists(path_dcc_object_node):
        with open(
            path_dcc_object_node,
            'r',
        ) as openfile:
            return json.load(openfile)
    raise Exception('No dcc object "{}" exists in Unreal project')


def connect_object(node_name, asset_info, logger):
    '''Store metadata and save the Unreal asset given by *node_name*, based on *asset_info*'''
    asset = get_asset_by_path(node_name)
    unreal.EditorAssetLibrary.set_metadata_tag(
        asset,
        asset_const.NODE_SNAPSHOT_METADATA_TAG
        if asset_info.get(asset_const.IS_SNAPSHOT)
        else asset_const.NODE_METADATA_TAG,
        str(asset_info.get(asset_const.ASSET_INFO_ID)),
    )

    # Have Unreal save the asset as it has been modified
    logger.debug('Saving asset: {}'.format(node_name))
    unreal.EditorAssetLibrary.save_asset(node_name)

    # As it has been saved, restore modification date to be the same as the imported component.
    # Otherwise asset will appear out of sync in ftrack.
    if asset_info.get(asset_const.IS_SNAPSHOT):
        component_path = asset_info.get(asset_const.COMPONENT_PATH)
        asset_filesystem_path = (
            unreal_file_utils.asset_path_to_filesystem_path(node_name)
        )
        file_size_remote = os.path.getsize(component_path)
        file_size_local = os.path.getsize(asset_filesystem_path)
        mod_date_remote = os.path.getmtime(component_path)

        stat = os.stat(asset_filesystem_path)
        os.utime(asset_filesystem_path, times=(stat.st_atime, mod_date_remote))
        logger.debug(
            'Restored file modification time: {} on asset: {} (size: {}, local size: {})'.format(
                mod_date_remote,
                asset_filesystem_path,
                file_size_remote,
                file_size_local,
            )
        )


def conditional_remove_metadata_tag(node_name, metadata_tag):
    '''Remove *metadata_tag* from the given *node_name*, returns True if found'''
    asset = get_asset_by_path(node_name)
    ftrack_value = unreal.EditorAssetLibrary.get_metadata_tag(
        asset, metadata_tag
    )
    if ftrack_value:
        unreal.EditorAssetLibrary.remove_metadata_tag(asset, metadata_tag)
        # Have Unreal save the asset as it has been modified
        unreal.EditorAssetLibrary.save_asset(node_name)
        return True
    else:
        return False
