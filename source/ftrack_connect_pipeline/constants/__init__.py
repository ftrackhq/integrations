# base name
_BASE_ = 'ftrack.pipeline'

# common stages
CONTEXT = 'context'

# common events
CONTEXT_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, CONTEXT)

# external events
REGISTER_ASSET_TOPIC = '{}.asset.register_assets'.format(_BASE_)
PIPELINE_RUN_TOPIC = '{}.host.run'.format(_BASE_)

# environment variables
PIPELINE_ASSET_PATH_ENV = 'FTRACK_PIPELINE_ASSET_PATH'

# avoid circular dependencies
from ftrack_connect_pipeline.constants.load import *
from ftrack_connect_pipeline.constants.publish import *
