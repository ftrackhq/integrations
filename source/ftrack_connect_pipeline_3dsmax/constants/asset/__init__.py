# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils

FTRACK_ASSET_CLASS_ID = (0x5c8d275e, 0x677d591c)
FTRACK_PLUGIN_TYPE = 'FtrackAssetHelper'

#Load Modes
IMPORT_MODE = 'Import'
OBJECT_XREF_MODE = 'Object XRef'
SCENE_XREF_MODE = 'Scene XRef'
OPEN_MODE = 'Open'


LOAD_MODES = {
    OPEN_MODE: max_utils.open_scene,
    IMPORT_MODE: max_utils.merge_max_file,
    SCENE_XREF_MODE: max_utils.import_scene_XRef,
    OBJECT_XREF_MODE: max_utils.import_obj_XRefs,
}


from ftrack_connect_pipeline.constants.asset.v2 import *
from ftrack_connect_pipeline.constants.asset.versions_mapping import *