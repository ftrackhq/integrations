_BASE_ = 'ftrack.pipeline'

CONTEXT    = 'context'
COLLECTORS = 'collectors'
VALIDATORS = 'validators'
EXTRACTORS = 'extractors'
PUBLISHERS = 'publishers'

REGISTER_ASSET_TOPIC = '{}.asset.register_assets'.format(_BASE_)
PIPELINE_RUN_TOPIC = '{}.host.run'.format(_BASE_)


CONTEXT_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, CONTEXT)
COLLECTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, COLLECTORS)
VALIDATORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, VALIDATORS)
EXTRACTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, EXTRACTORS)
PUBLISHERS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, PUBLISHERS)


PIPELINE_ASSET_PATH_ENV = 'FTRACK_PIPELINE_ASSET_PATH'


PUBLISH_ORDER = [
    CONTEXT,
    COLLECTORS,
    VALIDATORS,
    EXTRACTORS,
    PUBLISHERS
]