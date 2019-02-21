# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.constants import _BASE_

LOAD = 'load'
# Load stages.
IMPORTERS = 'importer'

# Load events.
IMPORTERS_PLUGIN_TOPIC = '{}.{}.{{}}'.format(_BASE_, IMPORTERS)

