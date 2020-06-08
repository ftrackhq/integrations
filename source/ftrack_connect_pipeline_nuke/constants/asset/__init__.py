# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils

FTRACK_PLUGIN_TYPE = 'ftracktab'

# Load Modes
IMPORT_MODE = 'Import'
OPEN_MODE = 'Open'
REFERENCE_MODE = 'Reference'


LOAD_MODES = {
    OPEN_MODE: nuke_utils.open_scene,
    IMPORT_MODE: nuke_utils.import_scene,
    REFERENCE_MODE: nuke_utils.reference_scene,
}

from ftrack_connect_pipeline.constants.asset.v2 import *
from ftrack_connect_pipeline.constants.asset.versions_mapping import *
