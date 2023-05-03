# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.constants import plugin

#: Loader plugin type for finalizer plugins
PLUGIN_LOADER_FINALIZER_TYPE = 'loader.{}'.format(
    plugin._PLUGIN_FINALIZER_TYPE
)
#: Loader plugin type for post finalizer plugins
PLUGIN_LOADER_POST_FINALIZER_TYPE = 'loader.{}'.format(
    plugin._PLUGIN_POST_FINALIZER_TYPE
)
#: Loader plugin type for pre finalizer plugins
PLUGIN_LOADER_PRE_FINALIZER_TYPE = 'loader.{}'.format(
    plugin._PLUGIN_PRE_FINALIZER_TYPE
)
#: Loader plugin type for context plugins
PLUGIN_LOADER_CONTEXT_TYPE = 'loader.{}'.format(plugin._PLUGIN_CONTEXT_TYPE)
#: Loader plugin type for collector plugins
PLUGIN_LOADER_COLLECTOR_TYPE = 'loader.{}'.format(
    plugin._PLUGIN_COLLECTOR_TYPE
)
#: Loader plugin type for importer plugins
PLUGIN_LOADER_IMPORTER_TYPE = 'loader.{}'.format(plugin._PLUGIN_IMPORTER_TYPE)
#: Loader plugin type for post import plugins
PLUGIN_LOADER_POST_IMPORTER_TYPE = 'loader.{}'.format(
    plugin._PLUGIN_POST_IMPORTER_TYPE
)
