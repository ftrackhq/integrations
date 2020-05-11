-- Copyright (c) 2016 ftrack

plugin Helper FtrackAssetHelper
name:"FtrackAssetHelper"
classID:#(0x5c8d275e, 0x677d591c)
invisible:true
category:"Ftrack"
extends:dummy
(
    parameters pblock
    (
        assetId type:#string default:""
        assetVersion type:#integer default:0
        assetPath type:#string default:""
        assetTake type:#string default:""
        assetType type:#string default:""
        assetComponentId type:#string default:""
        assetImportMode type:#string default:""
        alembicImportArgs type:#string default:""
        asset_id type:#string default:""
        version_id type:#string default:""
        version_number type:#integer default:0
        component_path type:#string default:""
        component_name type:#string default:""
        asset_type type:#string default:""
        component_id type:#string default:""
        asset_load_mode type:#string default:""
        alembic_import_args type:#string default:""
    )
)
