# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

UI = 'qt'

# Base name.
_BASE_ = 'ftrack.pipeline'

PIPELINE_UPDATE_UI = '{}.QtClient.update'.format(_BASE_)
PIPELINE_RUN_PLUGIN_TOPIC = '{}.run'.format(_BASE_)

# Avoid circular dependencies.
from ftrack_connect_pipeline_qt.constants.icons import *
