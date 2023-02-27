# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
from functools import wraps

import unreal

#### MISC ####


def run_in_main_thread(f):
    '''Make sure a function runs in the main Unreal thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        # Multithreading is disabled for Unreal integration
        return f(*args, **kwargs)

    return decorated


# Stored project data


def get_project_settings():
    '''Read and return settings from the Unreal project.'''
    settings_path = os.path.join(
        asset_const.FTRACK_ROOT_PATH,
        asset_const.PROJECT_SETTINGS_FILE_NAME,
    )
    if not os.path.exists(settings_path):
        return {}
    return json.load(open(settings_path, 'r'))


def save_project_settings(settings):
    '''Write the project settings to the current Unreal project.'''
    settings_path = os.path.join(
        asset_const.FTRACK_ROOT_PATH,
        asset_const.PROJECT_SETTINGS_FILE_NAME,
    )
    if not os.path.exists(asset_const.FTRACK_ROOT_PATH):
        logger.info(
            'Creating Unreal project ftrack root: {}'.format(
                asset_const.FTRACK_ROOT_PATH
            )
        )
        os.makedirs(asset_const.FTRACK_ROOT_PATH)
    with open(settings_path, 'w') as f:
        json.dump(settings, f)
        logger.info(
            'Successfully saved Unreal project settings to: {}'.format(
                settings_path
            )
        )


def update_project_settings(settings):
    '''Update the project settings with the given *settings*.'''
    existing_settings = get_project_settings()
    existing_settings.update(settings)
    save_project_settings(existing_settings)


from ftrack_connect_pipeline_unreal.utils.bootstrap import *
from ftrack_connect_pipeline_unreal.utils.node import *
from ftrack_connect_pipeline_unreal.utils.file import *
from ftrack_connect_pipeline_unreal.utils.asset import *
from ftrack_connect_pipeline_unreal.utils.sequencer import *
