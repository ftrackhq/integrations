# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline.constants import plugin

#: Opener plugin type for finalizer plugins
PLUGIN_OPENER_FINALIZER_TYPE = 'opener.{}'.format(
    plugin._PLUGIN_FINALIZER_TYPE
)
#: Opener plugin type for post finalizer plugins
PLUGIN_OPENER_POST_FINALIZER_TYPE = 'opener.{}'.format(
    plugin._PLUGIN_POST_FINALIZER_TYPE
)
#: Opener plugin type for pre finalizer plugins
PLUGIN_OPENER_PRE_FINALIZER_TYPE = 'opener.{}'.format(
    plugin._PLUGIN_PRE_FINALIZER_TYPE
)
#: Opener plugin type for context plugins
PLUGIN_OPENER_CONTEXT_TYPE = 'opener.{}'.format(plugin._PLUGIN_CONTEXT_TYPE)
#: Opener plugin type for collector plugins
PLUGIN_OPENER_COLLECTOR_TYPE = 'opener.{}'.format(
    plugin._PLUGIN_COLLECTOR_TYPE
)
#: Opener plugin type for importer plugins
PLUGIN_OPENER_IMPORTER_TYPE = 'opener.{}'.format(plugin._PLUGIN_IMPORTER_TYPE)
#: Opener plugin type for post import plugins
PLUGIN_OPENER_POST_IMPORTER_TYPE = 'opener.{}'.format(
    plugin._PLUGIN_POST_IMPORTER_TYPE
)
