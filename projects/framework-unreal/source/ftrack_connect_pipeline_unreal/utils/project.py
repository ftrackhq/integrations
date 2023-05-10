# Stored project data
# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import os
import json

import unreal

import ftrack_connect_pipeline_unreal.constants as unreal_constants

logger = logging.getLogger(__name__)

# Unreal project operations


def get_project_path():
    '''Return the current Unreal project path.'''
    return unreal.SystemLibrary.get_project_directory()


def get_project_settings():
    '''Read and return settings from the Unreal project.'''
    settings_path = os.path.join(
        unreal_constants.FTRACK_ROOT_PATH,
        unreal_constants.PROJECT_SETTINGS_FILE_NAME,
    )
    if not os.path.exists(settings_path):
        return {}
    return json.load(open(settings_path, 'r'))


def save_project_settings(settings):
    '''Write the project settings to the current Unreal project.'''
    settings_path = os.path.join(
        unreal_constants.FTRACK_ROOT_PATH,
        unreal_constants.PROJECT_SETTINGS_FILE_NAME,
    )
    if not os.path.exists(unreal_constants.FTRACK_ROOT_PATH):
        logger.info(
            'Creating Unreal project ftrack root: {}'.format(
                unreal_constants.FTRACK_ROOT_PATH
            )
        )
        os.makedirs(unreal_constants.FTRACK_ROOT_PATH)
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
