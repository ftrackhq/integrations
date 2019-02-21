# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.constants import _BASE_, PIPELINE_REGISTER_TOPIC

PUBLISH = 'publish'

# Publish stages.
COLLECTORS = 'collector'
VALIDATORS = 'validator'
EXTRACTORS = 'extractor'
PUBLISHERS = 'publisher'


# Publish events.
COLLECTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(PIPELINE_REGISTER_TOPIC, COLLECTORS)
VALIDATORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(PIPELINE_REGISTER_TOPIC, VALIDATORS)
EXTRACTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(PIPELINE_REGISTER_TOPIC, EXTRACTORS)
PUBLISHERS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(PIPELINE_REGISTER_TOPIC, PUBLISHERS)
