# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

import ftrack_connect_pipeline_unreal.constants as unreal_constants


def get_all_sequences(as_names=True):
    '''
    Returns a list of all sequence assets in the project If *as_names* is True,
    the asset name will be returned instead of the asset itself.
    '''
    result = []
    top_level_asset_path = {
        "package_name": "/Script/LevelSequence",
        "asset_name": "LevelSequence",
    }
    all_seq_asset_data = (
        unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(
            top_level_asset_path
        )
    )
    for _seq in all_seq_asset_data:
        if str(_seq.package_path).startswith(unreal_constants.GAME_ROOT_PATH):
            if as_names:
                result.append(str(_seq.asset_name))
                continue
            result.append(_seq.get_asset())

    return result
