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
        assetVersionId type:#string default:""
        assetVersion type:#integer default:0
        assetPath type:#string default:""
        assetTake type:#string default:""
        assetType type:#string default:""
        assetComponentId type:#string default:""
        assetImportMode type:#string default:""
        alembicImportArgs type:#string default:""
    )
)
