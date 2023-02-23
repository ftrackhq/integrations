# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import unreal


def sanitize_asset_path(asset_path):
    '''Convert given *asset_path* to a content-browser like path'''
    # TODO: should ask epic at some point to get the full path as its shown in
    #  the content browser so we don't have to "magically" change it here
    asset_path_sanitized = asset_path.replace('/Game', 'Content')
    return asset_path_sanitized


def ftrack_asset_path_exist(root_context_id, asset_path, session):
    '''Check if the given *full_ftrack_path* exist in the ftrack platform'''
    parent_context = session.query(
        'Context where id is "{}"'.format(root_context_id)
    ).one()
    if not parent_context:
        return False
    full_ftrack_path = sanitize_asset_path(asset_path)
    # Split asset path in array parts
    asset_path_parts = full_ftrack_path.split('/')
    # Get index of the root to support full path and asset path
    if parent_context['name'] not in asset_path_parts:
        start_idx = None
    else:
        start_idx = asset_path_parts.index(parent_context['name'])
    if start_idx or start_idx == 0:
        asset_path_parts = asset_path_parts[start_idx + 1 :]

    # Check from the root forward
    for index, part in enumerate(asset_path_parts):
        # Check if current part already exists
        child_context = session.query(
            'select id,name from Context where parent.id is "{0}" and name="{1}"'.format(
                parent_context['id'], part
            )
        ).first()
        if not child_context:
            return False
        parent_context = child_context
    return True


def get_ftrack_ancestors_names(ftrack_object):
    '''Returns ancestor names of the given ftrack_object'''
    return list(x['name'] for x in list(ftrack_object['ancestors']))


def get_full_ftrack_asset_path(root_context_id, asset_path, session):
    '''Given the *root_context_id* and the *asset_path*,
    returns the full path for the ftrack platform'''
    # Sanitize asset_path
    asset_path_sanitized = sanitize_asset_path(asset_path)
    # Get context(AB,Asset,Folder) ftrack object of the root_context_id
    parent_context = session.query(
        'Context where id is "{}"'.format(root_context_id)
    ).one()
    if not parent_context:
        raise Exception(
            'Could not find the root context object in ftrack, '
            'Please make sure the Root is created in your project.'
        )
    # Get project ftrack object from where our root_context_id is pointing.
    project = session.query(
        'Project where id="{}"'.format(parent_context['project_id'])
    ).one()

    # Get ancestors from root to project
    ancestor_names = get_ftrack_ancestors_names(parent_context)

    # Generate full path
    full_path = os.path.join(
        project['name'],
        *ancestor_names,
        parent_context['name'],
        *asset_path_sanitized.split('/')
    )
    return full_path.replace("\\", "/")


def filesystem_asset_path_to_asset_path(full_asset_path):
    '''Converts a full asset filesystem path to an asset path'''
    root_content_dir = (
        unreal.SystemLibrary.get_project_content_directory().replace(
            '/', os.sep
        )
    )
    if len(full_asset_path) > len(root_content_dir):
        result = '{}Game{}{}'.format(
            os.sep, os.sep, full_asset_path[len(root_content_dir) :]
        )
    else:
        result = full_asset_path  # Already an asset path
    return os.path.join(
        os.path.dirname(result), os.path.splitext(os.path.basename(result))[0]
    ).replace(
        '\\', '/'
    )  # Remove extension


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
    if asset_path.lower().startswith('/game/'):
        asset_path = asset_path[6:]  # Remove /Game/ prefix
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
