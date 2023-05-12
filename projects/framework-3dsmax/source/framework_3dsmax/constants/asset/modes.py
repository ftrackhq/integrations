# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_3dsmax import utils as max_utils

# Load Modes
IMPORT_MODE = 'import'
# TODO: to be implemented
# OBJECT_XREF_MODE = 'object XRef'
REFERENCE_MODE = 'scene XRef'
OPEN_MODE = 'open'

LOAD_MODES = {
    OPEN_MODE: max_utils.open_file,
    IMPORT_MODE: max_utils.import_file,
    REFERENCE_MODE: max_utils.reference_file,
    # OBJECT_XREF_MODE: max_utils.import_obj_XRefs,
}
