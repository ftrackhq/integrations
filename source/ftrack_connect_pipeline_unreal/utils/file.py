# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import unreal

### FILE OPERATIONS ###


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
