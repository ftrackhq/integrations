# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

#: Default ui type for ftrack_connect_pipeline
UI_TYPE = None
#: Default host type for ftrack_connect_pipeline
HOST_TYPE = 'python'

#: Base name for events
_BASE_ = 'ftrack.pipeline'

# Common steps.
#: Contexts step group.
CONTEXTS = 'contexts'
#: Finalizers step group.
FINALIZERS = 'finalizers'
#: Components step group.
COMPONENTS = 'components'

STEPS_ORDER = [CONTEXTS, COMPONENTS, FINALIZERS]

# Common steps types.
#: Contexts step type.
CONTEXT = 'context'
#: Finalizers step type.
FINALIZER = 'finalizer'
#: Components step type.
COMPONENT = 'component'

# Component stages.
#: Collector component stage name.
COLLECTOR = 'collector'
#: Validator component stage name.
VALIDATOR = 'validator'
#: Output component stage name.
OUTPUT = 'output'
#: Importer component stage name.
IMPORTER = 'importer'
#: Post_import component stage name.
POST_IMPORT = 'post_import'

# Common definition types.
#: Loader definition.
LOADER = 'loader'
#: Publisher definition.
PUBLISHER = 'publisher'


# External events.
#: Pipeline register topic event. Published by the
#: :class:`~ftrack_connect_pipeline.host.Host` and used to register
#: the definitions module.
#: `Definitions Docs <http://packages.python.org/an_example_pypi_project/>`_
PIPELINE_REGISTER_TOPIC = '{}.register'.format(_BASE_)
#: Pipeline run plugin topic event. Used to run the plugins. Published in
#: :meth:`~ftrack_connect_pipeline.asset.FtrackAssetBase.change_version` and
#: :meth:`~ftrack_connect_pipeline.host.engine.BaseEngine._run_plugin`.
#: Subscribed to run the plugins in
#: :meth:`~ftrack_connect_pipeline.plugin.BasePlugin.register`
PIPELINE_RUN_PLUGIN_TOPIC = '{}.run'.format(_BASE_)
#: Pipeline discover plugin topic event. Used to discover the plugins. Published
#: in :meth:`~ftrack_connect_pipeline.host.validation.PluginDiscoverValidation._discover_plugin`,
#: Subscribed to discover the plugins in
#: :meth:`~ftrack_connect_pipeline.plugin.BasePlugin.register`
PIPELINE_DISCOVER_PLUGIN_TOPIC = '{}.discover'.format(_BASE_)
#: Pipeline host run plugin topic event. Used to communicate between client and
#: host, by the host connection to make the host run the plugin. the plugins.
#: Published in :meth:`~ftrack_connect_pipeline.client.HostConnection.run`,
#: and Subscribed in
#: :meth:`~ftrack_connect_pipeline.host.on_register_definition`
PIPELINE_HOST_RUN = '{}.host.run'.format(_BASE_)
#: Pipeline client notification topic event. Used to communicate the result of
#: the plugin execution from host to the client.
#: Published in :meth:`~ftrack_connect_pipeline.host.engine.BaseEngine._notify_client`,
#: and Subscribed in
#: :meth:`~ftrack_connect_pipeline.client.on_client_notification`
PIPELINE_CLIENT_NOTIFICATION = '{}.client.notification'.format(_BASE_)
#: Pipeline client progress notification topic event. Used to communicate the result of
#: the steps execution from host to the client.
#: Published in :meth:`~ftrack_connect_pipeline.host.engine.BaseLoaderPublisherEngine._notify_progress_client`,
#: and Subscribed in
#: :meth:`~ftrack_connect_pipeline.client.on_client_progress_notification`
PIPELINE_CLIENT_PROGRESS_NOTIFICATION = (
    '{}.client.progress.notification'.format(_BASE_)
)
#: Pipeline Discover host topic event. Used to discover available hosts.
#: Published in :meth:`~ftrack_connect_pipeline.client._discover_hosts`,
#: and Subscribed in
#: :meth:`~ftrack_connect_pipeline.host.on_register_definition`
PIPELINE_DISCOVER_HOST = '{}.host.discover'.format(_BASE_)

# Launch a widget within a client
PIPELINE_WIDGET_LAUNCH = '{}.client.launch'.format(_BASE_)

# Avoid circular dependencies.
from ftrack_connect_pipeline.constants.plugin.load import *
from ftrack_connect_pipeline.constants.plugin.publish import *
from ftrack_connect_pipeline.constants.plugin.asset_manager import *
from ftrack_connect_pipeline.constants.event import *
from ftrack_connect_pipeline.constants.status import *
