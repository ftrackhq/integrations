# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_unreal.utils import (
    file as unreal_file_utils,
)

# Load Modes
IMPORT_MODE = 'import'

LOAD_MODES = {
    IMPORT_MODE: unreal_file_utils.import_file,
}
