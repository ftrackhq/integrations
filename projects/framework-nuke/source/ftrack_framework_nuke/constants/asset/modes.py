# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_nuke import utils as nuke_utils

# Load Modes
IMPORT_MODE = 'import'
OPEN_MODE = 'open'
REFERENCE_MODE = 'reference'


LOAD_MODES = {
    OPEN_MODE: nuke_utils.open_script,
    IMPORT_MODE: nuke_utils.import_script,
    REFERENCE_MODE: nuke_utils.reference_script,
}
