# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.constants import plugin

#: Publisher plugin type for finalizer plugins
PLUGIN_PUBLISHER_FINALIZER_TYPE = 'publisher.{}'.format(
    plugin._PLUGIN_FINALIZER_TYPE
)
#: Publisher plugin type for post finalizer plugins
PLUGIN_PUBLISHER_POST_FINALIZER_TYPE = 'publisher.{}'.format(
    plugin._PLUGIN_POST_FINALIZER_TYPE
)
#: Publisher plugin type for pre finalizer plugins
PLUGIN_PUBLISHER_PRE_FINALIZER_TYPE = 'publisher.{}'.format(
    plugin._PLUGIN_PRE_FINALIZER_TYPE
)
#: Publisher plugin type for context plugins
PLUGIN_PUBLISHER_CONTEXT_TYPE = 'publisher.{}'.format(
    plugin._PLUGIN_CONTEXT_TYPE
)
#: Publisher plugin type for collector plugins
PLUGIN_PUBLISHER_COLLECTOR_TYPE = 'publisher.{}'.format(
    plugin._PLUGIN_COLLECTOR_TYPE
)
#: Publisher plugin type for validator plugins
PLUGIN_PUBLISHER_VALIDATOR_TYPE = 'publisher.{}'.format(
    plugin._PLUGIN_VALIDATOR_TYPE
)
#: Publisher plugin type for exporters plugins
PLUGIN_PUBLISHER_EXPORTER_TYPE = 'publisher.{}'.format(
    plugin._PLUGIN_EXPORTER_TYPE
)
