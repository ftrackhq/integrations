# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import unreal

### FILE OPERATIONS ###

# TODO: Find a better name for this function. This is not a relative path.
def get_context_relative_path(session, ftrack_task):
    # location.
    links_for_task = session.query(
        'select link from Task where id is "{}"'.format(ftrack_task['id'])
    ).first()['link']
    relative_path = ""
    # remove the project
    links_for_task.pop(0)
    for link in links_for_task:
        relative_path += link['name'].replace(' ', '_')
        relative_path += '/'
    return relative_path


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
