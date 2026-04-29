# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_asset_manager.asset import constants as asset_const

# Maya-specific constants
FTRACK_PLUGIN_ID = 0x190319
FTRACK_PLUGIN_TYPE = 'ftrackAssetNode'
LOCKED = 'locked'
ASSET_LINK = 'asset_link'

# Load modes
IMPORT_MODE = 'import'
REFERENCE_MODE = 'reference'
OPEN_MODE = 'open'

# Re-export common constants for convenience
DCC_OBJECT_NAME = asset_const.DCC_OBJECT_NAME
ASSET_ID = asset_const.ASSET_ID
ASSET_NAME = asset_const.ASSET_NAME
CONTEXT_PATH = asset_const.CONTEXT_PATH
ASSET_TYPE_NAME = asset_const.ASSET_TYPE_NAME
VERSION_ID = asset_const.VERSION_ID
VERSION_NUMBER = asset_const.VERSION_NUMBER
COMPONENT_PATH = asset_const.COMPONENT_PATH
COMPONENT_NAME = asset_const.COMPONENT_NAME
COMPONENT_ID = asset_const.COMPONENT_ID
LOAD_MODE = asset_const.LOAD_MODE
ASSET_INFO_OPTIONS = asset_const.ASSET_INFO_OPTIONS
REFERENCE_OBJECT = asset_const.REFERENCE_OBJECT
IS_LATEST_VERSION = asset_const.IS_LATEST_VERSION
ASSET_INFO_ID = asset_const.ASSET_INFO_ID
DEPENDENCY_IDS = asset_const.DEPENDENCY_IDS
OBJECTS_LOADED = asset_const.OBJECTS_LOADED
