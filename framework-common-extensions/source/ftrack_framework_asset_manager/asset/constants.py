# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""
Asset Manager Constants Module

This module defines all the constant keys used throughout the asset management system
for consistent data access and serialization.
"""

# Asset identifier keys
ASSET_ID = "asset_id"
ASSET_NAME = "asset_name"
CONTEXT_PATH = "context_path"
ASSET_TYPE_NAME = "asset_type_name"
VERSION_ID = "version_id"
VERSION_NUMBER = "version_number"
COMPONENT_PATH = "component_path"
COMPONENT_NAME = "component_name"
COMPONENT_ID = "component_id"
LOAD_MODE = "load_mode"
ASSET_INFO_OPTIONS = "asset_info_options"
REFERENCE_OBJECT = "reference_object"
IS_LATEST_VERSION = "is_latest_version"
ASSET_INFO_ID = "asset_info_id"
DEPENDENCY_IDS = "dependency_ids"
OBJECTS_LOADED = "objects_loaded"
DCC_OBJECT_NAME = "dcc_object_name"

# List of all keys for validation and iteration
KEYS = [
    ASSET_ID,
    ASSET_NAME,
    CONTEXT_PATH,
    ASSET_TYPE_NAME,
    VERSION_ID,
    VERSION_NUMBER,
    COMPONENT_PATH,
    COMPONENT_NAME,
    COMPONENT_ID,
    LOAD_MODE,
    ASSET_INFO_OPTIONS,
    REFERENCE_OBJECT,
    IS_LATEST_VERSION,
    ASSET_INFO_ID,
    DEPENDENCY_IDS,
    OBJECTS_LOADED,
    DCC_OBJECT_NAME,
]

# Version constant
VERSION = "1.0.0"
