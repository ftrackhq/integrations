-- Copyright (c) 2016 ftrack

plugin Helper FtrackAssetHelper
name:"FtrackAssetHelper"
classID:#(0x5c8d275e, 0x677d591c)
invisible:true
category:"Ftrack"
version: 2
extends:dummy
(
    parameters pblock
    (
        asset_name type:#string default:""
        asset_id type:#string default:""
        version_id type:#string default:""
        version_number type:#integer default:0
        component_path type:#string default:""
        component_name type:#string default:""
        asset_type type:#string default:""
        component_id type:#string default:""
        asset_info_options type:#string default:""
    )
)
