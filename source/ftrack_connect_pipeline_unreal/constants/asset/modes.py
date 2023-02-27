# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_unreal import utils

# Load Modes
IMPORT_MODE = 'import'

LOAD_MODES = {
    IMPORT_MODE: utils.import_file,
}
