# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_houdini.utils import custom_commands as houdini_utils

# Load Modes
IMPORT_MODE = 'Import'
MERGE_MODE = 'Merge'
OPEN_MODE = 'Open'

LOAD_MODES = {
    IMPORT_MODE: houdini_utils.import_scene,
    MERGE_MODE: houdini_utils.merge_scene,
    OPEN_MODE: houdini_utils.open_scene,
}