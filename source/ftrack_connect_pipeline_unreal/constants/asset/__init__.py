# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import unreal

FTRACK_PLUGIN_TYPE = 'ftrackAssetNode'
ASSET_LINK = 'asset_link'
NODE_METADATA_TAG = "ftrack"
FTRACK_ROOT_PATH = os.path.realpath(
    os.path.join(unreal.SystemLibrary.get_project_saved_directory(), "ftrack")
)
PROJECT_SETTINGS_FILE_NAME = "project_settings.json"

from ftrack_connect_pipeline.constants.asset import *
