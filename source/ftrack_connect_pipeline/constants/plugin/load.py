# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.constants import plugin

PLUGIN_LOADER_FINALISER_TYPE = 'loader.{}'.format(plugin._PLUGIN_FINALISER_TYPE)
PLUGIN_LOADER_CONTEXT_TYPE = 'loader.{}'.format(plugin._PLUGIN_CONTEXT_TYPE)
PLUGIN_LOADER_COLLECTOR_TYPE = 'loader.{}'.format(plugin._PLUGIN_COLLECTOR_TYPE)
PLUGIN_LOADER_IMPORTER_TYPE = 'loader.{}'.format(plugin._PLUGIN_IMPORTER_TYPE)
PLUGIN_LOADER_POST_IMPORT_TYPE = 'loader.{}'.format(plugin._PLUGIN_POST_IMPORT_TYPE)
