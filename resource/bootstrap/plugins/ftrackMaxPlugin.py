# :copyright: Copyright (c) 2014-2022 ftrack

import pymxs

from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


def register_ftrack_asset_helper():
    pymxs.runtime.execute(
        """
        -- Copyright (c) 2022 ftrack
        plugin Helper {plugin_name}
        name:"{plugin_name}"
        classID:#{class_id}
        invisible:true
        category:"ftrack"
        version: {version}
        extends:dummy
        (
            parameters pblock
            (
                {locked} type:#boolean default:False
                {asset_link} type:#string default:""
                {dependency_ids} type:#string default:""
                {asset_id} type:#string default:""
                {context_path} type:#string default:""
                {asset_name} type:#string default:""
                {asset_type_name} type:#string default:"" 
                {version_id} type:#string default:""
                {version_number} type:#integer default:0
                {component_path} type:#string default:""
                {component_name} type:#string default:""
                {component_id} type:#string default:""
                {load_mode} type:#string default:""
                {asset_info_options} type:#string default:""
                {reference_object} type:#string default:""
                {is_latest_version} type:#boolean default:False
                {asset_info_id} type:#string default:""
                {objects_loaded} type:#boolean default:False
            )
        )
        """.format(
            plugin_name=asset_const.FTRACK_PLUGIN_TYPE,
            class_id=asset_const.FTRACK_PLUGIN_ID,
            version=asset_const.VERSION,
            locked=asset_const.LOCKED,
            asset_link=asset_const.ASSET_LINK,
            dependency_ids=asset_const.DEPENDENCY_IDS,
            asset_id=asset_const.ASSET_ID,
            context_path=asset_const.CONTEXT_PATH,
            asset_name=asset_const.ASSET_NAME,
            asset_type_name=asset_const.ASSET_TYPE_NAME,
            version_id=asset_const.VERSION_ID,
            version_number=asset_const.VERSION_NUMBER,
            component_path=asset_const.COMPONENT_PATH,
            component_name=asset_const.COMPONENT_NAME,
            component_id=asset_const.COMPONENT_ID,
            load_mode=asset_const.LOAD_MODE,
            asset_info_options=asset_const.ASSET_INFO_OPTIONS,
            reference_object=asset_const.REFERENCE_OBJECT,
            is_latest_version=asset_const.IS_LATEST_VERSION,
            asset_info_id=asset_const.ASSET_INFO_ID,
            objects_loaded=asset_const.OBJECTS_LOADED,
        )
    )


register_ftrack_asset_helper()
