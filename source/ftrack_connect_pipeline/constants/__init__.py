# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

UI_TYPE = None
HOST_TYPE = 'python'

# Base name.
_BASE_ = 'ftrack.pipeline'

# Common stages.
CONTEXTS = 'contexts'
FINALIZERS = 'finalizers'
COMPONENTS = 'components'

# component stages.
COLLECTOR = 'collector'
VALIDATOR = 'validator'
OUTPUT = 'output'
IMPORTER = 'importer'
POST_IMPORT = 'post_import'

# External events.
PIPELINE_REGISTER_TOPIC = '{}.register'.format(_BASE_)
PIPELINE_RUN_PLUGIN_TOPIC = '{}.run'.format(_BASE_)

PIPELINE_DISCOVER_PLUGIN_TOPIC = '{}.discover'.format(_BASE_)

PIPELINE_HOST_RUN = '{}.host.run'.format(_BASE_)
PIPELINE_CLIENT_NOTIFICATION = '{}.client.notification'.format(_BASE_)
PIPELINE_DISCOVER_HOST = '{}.host.discover'.format(_BASE_)

# Avoid circular dependencies.
from ftrack_connect_pipeline.constants.plugin.load import *
from ftrack_connect_pipeline.constants.plugin.publish import *
from ftrack_connect_pipeline.constants.plugin.asset_manager import *
from ftrack_connect_pipeline.constants.environments import *
from ftrack_connect_pipeline.constants.event import *
from ftrack_connect_pipeline.constants.status import *
