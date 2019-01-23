from ftrack_connect_pipeline.constants import _BASE_

PUBLISH = 'publish'

# publish stages
COLLECTORS = 'collectors'
VALIDATORS = 'validators'
EXTRACTORS = 'extractors'
PUBLISHERS = 'publishers'


# publish events
COLLECTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, COLLECTORS)
VALIDATORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, VALIDATORS)
EXTRACTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, EXTRACTORS)
PUBLISHERS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, PUBLISHERS)
