# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
from functools import wraps

import unreal

from ftrack_connect_pipeline_unreal.constants import asset as asset_const

#### MISC ####


def run_in_main_thread(f):
    '''Make sure a function runs in the main Unreal thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        # Multithreading is disabled for Unreal integration
        return f(*args, **kwargs)

    return decorated


def prepare_load_task(session, context_data, data, options):
    '''Prepare loader import task based on *data* and *context_data* supplied, based on *options*.'''

    paths_to_import = []
    for collector in data:
        paths_to_import.append(
            collector['result'].get(asset_const.COMPONENT_PATH)
        )

    component_path = paths_to_import[0]

    # Check if it exists
    if not os.path.exists(component_path):
        raise Exception(
            'The asset file does not exist: "{}"'.format(component_path)
        )

    task = unreal.AssetImportTask()

    task.filename = component_path

    # Determine the folder to import to
    selected_context_browser_path = (
        unreal.EditorUtilityLibrary.get_current_content_browser_path()
    )
    if selected_context_browser_path is not None:
        import_path = selected_context_browser_path
    else:
        import_path = '/Game'

    task.destination_path = import_path.replace(' ', '_')
    task.destination_name = context_data['asset_name'].replace(' ', '_')

    task.replace_existing = options.get('ReplaceExisting', True)
    task.automated = options.get('Automated', True)
    task.save = options.get('Save', True)

    return task, component_path


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


def assets_to_paths(assets):
    result = []
    for asset in assets:
        result.append(asset.get_path_name())
    return result
