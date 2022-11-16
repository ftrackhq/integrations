# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils

# Load Modes
IMPORT_MODE = 'Import'
# TODO: to be implemented
# OBJECT_XREF_MODE = 'Object XRef'
REFERENCE_MODE = 'Scene XRef'
OPEN_MODE = 'Open'

LOAD_MODES = {
    OPEN_MODE: max_utils.open_file,
    IMPORT_MODE: max_utils.import_file,
    REFERENCE_MODE: max_utils.reference_file,
    # OBJECT_XREF_MODE: max_utils.import_obj_XRefs,
}
