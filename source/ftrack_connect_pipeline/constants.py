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

# - PUBLISH ----------------------------------------------------------
PUBLISH = 'publish'
# publish stages
COLLECTORS = 'collectors'
VALIDATORS = 'validators'
EXTRACTORS = 'extractors'
PUBLISHERS = 'publishers'

# publish stack
PUBLISH_ORDER = [
    CONTEXT,
    COLLECTORS,
    VALIDATORS,
    EXTRACTORS,
    PUBLISHERS
]

# publish events
COLLECTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, COLLECTORS)
VALIDATORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, VALIDATORS)
EXTRACTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, EXTRACTORS)
PUBLISHERS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, PUBLISHERS)


# - LOAD ----------------------------------------------------------
LOAD = 'load'
# load stages
COMPONENTS = 'components'
INTEGRATORS = 'integrators'

# load stack
LOAD_ORDER = [
    CONTEXT,
    COMPONENTS,
    INTEGRATORS
]

# load events
COMPONENTS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, COMPONENTS)
INTEGRATORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, INTEGRATORS)




