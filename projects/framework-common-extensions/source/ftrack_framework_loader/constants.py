# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""Loader constants"""

# Plugin type constants
PLUGIN_LOADER_CONTEXT_TYPE = "loader.context"
PLUGIN_LOADER_COLLECTOR_TYPE = "loader.collector"
PLUGIN_LOADER_IMPORTER_TYPE = "loader.importer"
PLUGIN_LOADER_POST_IMPORTER_TYPE = "loader.post_importer"
PLUGIN_LOADER_PRE_FINALIZER_TYPE = "loader.pre_finalizer"
PLUGIN_LOADER_FINALIZER_TYPE = "loader.finalizer"
PLUGIN_LOADER_POST_FINALIZER_TYPE = "loader.post_finalizer"

# Pipeline stage names
STAGE_CONTEXT = "context"
STAGE_COLLECTOR = "collector"
STAGE_IMPORTER = "importer"
STAGE_POST_IMPORTER = "post_importer"
STAGE_PRE_FINALIZER = "pre_finalizer"
STAGE_FINALIZER = "finalizer"
STAGE_POST_FINALIZER = "post_finalizer"

# Method names
METHOD_INIT_NODES = "init_nodes"
METHOD_LOAD_ASSET = "load_asset"
METHOD_INIT_AND_LOAD = "init_and_load"
METHOD_RUN = "run"

# Component config keys
COMPONENT_NAME = "name"
COMPONENT_FILE_FORMATS = "file_formats"
COMPONENT_OPTIONAL = "optional"
COMPONENT_SELECTED = "selected"
COMPONENT_PLUGINS = "plugins"

# Store keys
STORE_CONTEXT_DATA = "context_data"
STORE_COLLECTED_PATHS = "collected_paths"
STORE_COMPONENT_RESULTS = "component_results"
STORE_ASSET_INFO = "asset_info"
STORE_DCC_OBJECT = "dcc_object"
STORE_LOADED_OBJECTS = "loaded_objects"
STORE_RESULTS = "results"
