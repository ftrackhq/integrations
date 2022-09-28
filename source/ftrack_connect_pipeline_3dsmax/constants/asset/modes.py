# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils

# Load Modes
IMPORT_MODE = 'import'
REFERENCE_MODE = 'reference'
OPEN_MODE = 'open'

LOAD_MODES = {
    OPEN_MODE: max_utils.open_file,
    IMPORT_MODE: max_utils.import_file,
    REFERENCE_MODE: max_utils.reference_file,
}
