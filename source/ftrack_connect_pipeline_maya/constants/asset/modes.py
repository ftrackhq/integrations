# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_maya import utils as maya_utils

# Load Modes
IMPORT_MODE = 'import'
REFERENCE_MODE = 'reference'
OPEN_MODE = 'open'

LOAD_MODES = {
    OPEN_MODE: maya_utils.open_file,
    IMPORT_MODE: maya_utils.import_file,
    REFERENCE_MODE: maya_utils.reference_file,
}
