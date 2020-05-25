# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import pymxs
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const

def register_ftrack_asset_helper():
    pymxs.runtime.execute(
        """
        -- Copyright (c) 2016 ftrack
        plugin Helper FtrackAssetHelper
        name:"{plugin_name}"
        classID:#{class_id}
        invisible:true
        category:"Ftrack"
        version: {version}
        extends:dummy
        (
            parameters pblock
            (
                {asset_name} type:#string default:""
                {asset_id} type:#string default:""
                {version_id} type:#string default:""
                {version_number} type:#integer default:0
                {component_path} type:#string default:""
                {component_name} type:#string default:""
                {asset_type} type:#string default:""
                {component_id} type:#string default:""
                {asset_info_options} type:#string default:""
            )
        )
        """.format(
            plugin_name=asset_const.FTRACK_PLUGIN_TYPE,
            class_id=asset_const.FTRACK_ASSET_CLASS_ID,
            version=asset_const.VERSION,
            asset_name=asset_const.ASSET_NAME,
            asset_id=asset_const.ASSET_ID,
            version_id=asset_const.VERSION_ID,
            version_number=asset_const.VERSION_NUMBER,
            component_path=asset_const.COMPONENT_PATH,
            component_name=asset_const.COMPONENT_NAME,
            asset_type=asset_const.ASSET_TYPE,
            component_id=asset_const.COMPONENT_ID,
            asset_info_options=asset_const.ASSET_INFO_OPTIONS,
        )
    )


register_ftrack_asset_helper()
