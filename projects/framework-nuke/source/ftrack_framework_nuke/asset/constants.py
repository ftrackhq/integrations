# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

FTRACK_PLUGIN_ID = 2386071295
FTRACK_PLUGIN_TYPE = 'ftracktab'
ASSET_LINK = 'asset_link'

from ftrack_framework_asset_manager.asset import constants as asset_const

KEYS = [
    asset_const.ASSET_INFO_ID,
    asset_const.ASSET_INFO_OPTIONS,
    asset_const.CONTEXT_PATH,
    asset_const.COMPONENT_NAME,
    asset_const.VERSION_ID,
    asset_const.LOAD_MODE,
    asset_const.OBJECTS_LOADED,
    asset_const.IS_LATEST_VERSION,
    asset_const.REFERENCE_OBJECT,
    asset_const.DEPENDENCY_IDS,
]
