# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from ftrack_connect_pipeline import constants


UI_TYPE = 'qt'
HOST_TYPE = constants.HOST_TYPE

# Base name.
_BASE_ = 'ftrack.pipeline'

# Avoid circular dependencies.
from ftrack_connect_pipeline_qt.constants.icons import *
