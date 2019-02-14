# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.constants import _BASE_

PUBLISH = 'publish'

# Publish stages.
COLLECTORS = 'collectors'
VALIDATORS = 'validators'
EXTRACTORS = 'extractors'
PUBLISHERS = 'publishers'


# Publish events.
COLLECTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, COLLECTORS)
VALIDATORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, VALIDATORS)
EXTRACTORS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, EXTRACTORS)
PUBLISHERS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, PUBLISHERS)
