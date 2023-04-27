# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

#: Name of the ftrack object to identify the loaded assets
DCC_OBJECT_NAME = '{}_ftrackdata_{}'

#: Asset id constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
ASSET_ID = 'asset_id'
#: Asset name constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
ASSET_NAME = 'asset_name'
#: context path constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
CONTEXT_PATH = 'context_path'
#: Asset type constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
ASSET_TYPE_NAME = 'asset_type_name'
#: Version id constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
VERSION_ID = 'version_id'
#: Version number constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
VERSION_NUMBER = 'version_number'
#: Component path constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
COMPONENT_PATH = 'component_path'
#: Component name constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
COMPONENT_NAME = 'component_name'
#: Component id constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
COMPONENT_ID = 'component_id'
#: Load Mode constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
LOAD_MODE = 'load_mode'
#: Asset info options constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
ASSET_INFO_OPTIONS = 'asset_info_options'
#: Reference object constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
# TODO: Change this constant name to something like DCC_OBJECT.
REFERENCE_OBJECT = 'reference_object'
#: Is Lates version constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
IS_LATEST_VERSION = 'is_latest_version'
#: Asset info ID constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
ASSET_INFO_ID = 'asset_info_id'
#: Dependency ids constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
DEPENDENCY_IDS = 'dependency_ids'
#: Is loaded constant identifier key for ftrack assets connected or used with
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
#: and the DCC ftrack plugin.
OBJECTS_LOADED = 'objects_loaded'

#: Identifier version of the asset constants and plugin.
VERSION = '1.0'

#: List of all the constants keys used for the
#: :class:`~ftrack_connect_pipeline.asset.asset_info.FtrackAssetInfo`
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
]
