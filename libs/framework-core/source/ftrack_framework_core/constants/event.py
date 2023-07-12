# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

#: Run the events of the session in remote mode
REMOTE_EVENT_MODE = 1
#: Run the events of the session in local mode
LOCAL_EVENT_MODE = 0

#: See event_table.md from :ref:`~framework_core.doc.developing.event_table.md` file for a better reference on eeach event.

#: Base name for events
_BASE_ = 'ftrack.integrations.framework'

#: Register definition topic event.
DISCOVER_DEFINITION_TOPIC = '{}.discover.definition'.format(_BASE_)
#: Discover plugin topic event, used to discover the plugins.
DISCOVER_PLUGIN_TOPIC = '{}.discover.plugin'.format(_BASE_)
#: Discover host topic event, used to discover available hosts.
DISCOVER_HOST_TOPIC = '{}.host.discover.host'.format(_BASE_)
#: Run plugin topic event used to run the plugins in the host.
HOST_RUN_PLUGIN_TOPIC = '{}.host.run.plugin'.format(_BASE_)
#: Pipeline host run plugin topic event, used to communicate between client and
#: host, by the host connection to make the host run the plugin.
HOST_RUN_DEFINITION_TOPIC = '{}.host.run.definition'.format(_BASE_)
#: Pipeline client notification topic event, used to communicate the result of
#: the plugin execution from host to the client.
NOTIFY_CLIENT_TOPIC = '{}.client.notify.client'.format(_BASE_)
#: Pipeline client progress notification topic event, used to communicate the result of
#: the steps execution from host to the client.
NOTIFY_PROGRESS_CLIENT_TOPIC = '{}.client.notify.progress'.format(_BASE_)
# Launch a widget within a client
CLIENT_LAUNCH_WIDGET_TOPIC = '{}.client.launch.widget'.format(_BASE_)
# The main host context has changed, sent from host or host connection (change context)
HOST_CONTEXT_CHANGED_TOPIC = '{}.host.context.change'.format(_BASE_)
# The host connection context has changed, sent from host connection to clients
CLIENT_CONTEXT_CHANGE_TOPIC = '{}.client.context.change'.format(_BASE_)
