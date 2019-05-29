# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

UI = 'qt'
HOST = '*'

# Base name.
_BASE_ = 'ftrack.pipeline'

# Common stages.
CONTEXT = 'context'

# External events.
PIPELINE_REGISTER_TOPIC = '{}.register'.format(_BASE_)
PIPELINE_RUN_PLUGIN_TOPIC = '{}.run'.format(_BASE_)

PIPELINE_DISCOVER_PLUGIN_TOPIC = '{}.discover'.format(_BASE_)

PIPELINE_REGISTER_DEFINITION_TOPIC = '{}.register.definition'.format(_BASE_)

PIPELINE_RUN_HOST_PUBLISHER = '{}.host.publish'.format(_BASE_)
PIPELINE_UPDATE_UI = '{}.client.update'.format(_BASE_)
PIPELINE_DISCOVER_HOST = '{}.host.discover'.format(_BASE_)
PIPELINE_CONNECT_CLIENT = '{}.client.connect'.format(_BASE_)

# Avoid circular dependencies.
from ftrack_connect_pipeline.constants.load import *
from ftrack_connect_pipeline.constants.publish import *
from ftrack_connect_pipeline.constants.environments import *
from ftrack_connect_pipeline.constants.event import *
from ftrack_connect_pipeline.constants.status import *
