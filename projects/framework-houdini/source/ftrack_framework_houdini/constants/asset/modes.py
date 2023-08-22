# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_houdini import utils as houdini_utils

# Load Modes
MERGE_MODE = 'merge'
IMPORT_MODE = 'import'
OPEN_MODE = 'open'

LOAD_MODES = {
    MERGE_MODE: houdini_utils.merge_scene,
    IMPORT_MODE: houdini_utils.import_scene,
    OPEN_MODE: houdini_utils.open_scene,
}
