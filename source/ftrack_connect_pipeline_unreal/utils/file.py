# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import clique

import unreal


def import_file(asset_import_task):
    '''Native import file function using the object unreal.AssetImportTask() given as *asset_import_task*'''
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(
        [asset_import_task]
    )
    return (
        asset_import_task.imported_object_paths[0]
        if len(asset_import_task.imported_object_paths or []) > 0
        else None
    )


# TODO: move this util to pipeline utils
def find_image_sequence(file_path):
    '''Try to find a continous image sequence in the *render_folder*, Unreal always names frames "Image.0001.png".
    Will return the clique parsable expression together with first and last frame number.
    '''

    is_dir = False
    if not file_path or not os.path.exists(os.path.dirname(file_path)):
        return None

    if os.path.isdir(file_path):
        is_dir = True
        folder_path = file_path
    else:
        folder_path = os.path.dirname(file_path)
    # Search folder for images sequence
    collections, remainder = clique.assemble(
        os.listdir(folder_path), minimum_items=1
    )
    if not collections:
        return None

    if is_dir:
        return os.path.join(folder_path, collections[0].format())
    for collection in collections:
        if collection.match(os.path.basename(file_path)):
            return os.path.join(folder_path, collection.format())

    return None
