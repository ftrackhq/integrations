# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_harmony import utils as harmony_utils

# Load Modes
IMPORT_MODE = 'import'
REFERENCE_MODE = 'reference'
OPEN_MODE = 'open'

LOAD_MODES = {
    OPEN_MODE: harmony_utils.open_file,
    IMPORT_MODE: harmony_utils.import_file,
    REFERENCE_MODE: harmony_utils.reference_file,
}
