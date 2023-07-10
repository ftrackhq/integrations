# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_framework_core.constants import plugin

#: Asset Manager plugin type for action plugins
PLUGIN_AM_ACTION_TYPE = 'asset_manager.{}'.format(plugin._PLUGIN_ACTION_TYPE)
#: Asset Manager plugin type for discover plugins
PLUGIN_AM_DISCOVER_TYPE = 'asset_manager.{}'.format(
    plugin._PLUGIN_DISCOVER_TYPE
)
#: Asset Manager plugin type for action plugins
PLUGIN_RESOLVE_TYPE = 'resolver.{}'.format(plugin._PLUGIN_RESOLVER_TYPE)
