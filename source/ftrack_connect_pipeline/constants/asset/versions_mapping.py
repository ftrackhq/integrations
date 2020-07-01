# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.constants.asset import v1, v2

#Legacy Parameters Mapping
V1_TO_V2_MAPPING = {
    v1.VERSION_ID: v2.VERSION_ID,
    v1.VERSION_NUMBER: v2.VERSION_NUMBER,
    v1.COMPONENT_PATH: v2.COMPONENT_PATH,
    v1.COMPONENT_NAME: v2.COMPONENT_NAME,
    v1.ASSET_TYPE: v2.ASSET_TYPE,
    v1.COMPONENT_ID: v2.COMPONENT_ID,
    v1.ASSET_INFO_OPTIONS: v2.ASSET_INFO_OPTIONS
}