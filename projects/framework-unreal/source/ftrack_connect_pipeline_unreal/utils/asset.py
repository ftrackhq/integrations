# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import unreal

import ftrack_connect_pipeline_unreal.constants as unreal_constants


def asset_path_to_filesystem_path(
    asset_path, root_content_dir=None, throw_on_error=True
):
    '''Converts *asset_path* to a full absolute asset filesystem path. Use the provided *root_content_dir*.'''
    if root_content_dir is None:
        root_content_dir = (
            unreal.SystemLibrary.get_project_content_directory().replace(
                '/', os.sep
            )
        )
    if asset_path.lower().startswith(unreal_constants.GAME_ROOT_PATH.lower()):
        asset_path = asset_path[
            len(unreal_constants.GAME_ROOT_PATH) + 1 :
        ]  # Remove /Game/ prefix
    asset_path = asset_path.replace('/', os.sep)  # Align to platform
    content_folder, asset_filename = os.path.split(asset_path)
    asset_filename = os.path.splitext(asset_filename)[0]  # Remove extension
    path = os.path.join(root_content_dir, content_folder, asset_filename)
    # Probe our way to finding out the extension as we can't tell from the asset path
    for ext in ['', '.uasset', '.umap']:
        result = '{}{}'.format(path, ext)
        if os.path.exists(result):
            return result
    if throw_on_error:
        raise Exception(
            'Could not determine asset "{}" files extension on disk!'.format(
                path
            )
        )
    else:
        return None


def get_asset_by_path(node_name):
    '''Get Unreal asset object by path'''
    if not node_name:
        return None
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_data = asset_registry.get_assets_by_package_name(
        os.path.splitext(node_name)[0]
    )
    if asset_data:
        return asset_data[0].get_asset()
    return None


def get_assets_by_class(class_name):
    '''Get all assets of a given Unreal class named *class_name*'''
    return [
        asset
        for asset in unreal.AssetRegistryHelpers.get_asset_registry().get_all_assets()
        if asset.get_class().get_name() == class_name
    ]
