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


def find_image_sequence(render_folder):
    '''Try to find a continous image sequence in the *render_folder*, Unreal always names frames "Image.0001.png".
    Will return the clique parsable expression together with first and last frame number.
    '''

    if not render_folder or not os.path.exists(render_folder):
        return None

    # Search folder for images sequence
    collections, remainder = clique.assemble(
        os.listdir(render_folder), minimum_items=1
    )

    # Pick first collection, ignore if there are multiple image sequences in the folder for now
    if collections:
        collection = collections[0]
        return os.path.join(render_folder, collection.format())

    return None
