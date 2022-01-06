# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils
#Load Modes
IMPORT_MODE = 'Import'
REFERENCE_MODE = 'Reference'
OPEN_MODE = 'Open'

LOAD_MODES = {
    OPEN_MODE: maya_utils.open_file,
    IMPORT_MODE: maya_utils.import_file,
    REFERENCE_MODE: maya_utils.reference_file
}
