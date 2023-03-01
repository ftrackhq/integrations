# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import unreal

HOST_TYPE = 'unreal'
UI_TYPE = 'unreal'

FTRACK_ROOT_PATH = os.path.realpath(
    os.path.join(unreal.SystemLibrary.get_project_saved_directory(), "ftrack")
)
PROJECT_SETTINGS_FILE_NAME = "project_settings.json"
GAME_ROOT_PATH = '/Game'
