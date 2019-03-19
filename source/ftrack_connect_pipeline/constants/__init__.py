# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

UI = 'qt'
HOST = '*'

# Base name.
_BASE_ = 'ftrack.pipeline'

# Common stages.
CONTEXT = 'context'

# Common events.
CONTEXT_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, CONTEXT)

# External events.
PIPELINE_REGISTER_TOPIC = '{}.register'.format(_BASE_)
PIPELINE_DEFINITION_TOPIC = '{}.definition'.format(_BASE_)


PIPELINE_RUN_PUBLISHER = '{}.host.publish'.format(_BASE_)


# Avoid circular dependencies.
from ftrack_connect_pipeline.constants.load import *
from ftrack_connect_pipeline.constants.publish import *
from ftrack_connect_pipeline.constants.environments import *
