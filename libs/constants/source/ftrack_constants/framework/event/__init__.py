# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

#: Run the events of the session in remote mode
REMOTE_EVENT_MODE = 1
#: Run the events of the session in local mode
LOCAL_EVENT_MODE = 0

#: See event_table.md from :ref:`~framework_core.doc.developing.event_table.md` file for a better reference on eeach event.

#: Base name for events
_BASE_ = 'ftrack.framework'

#: Register definition topic event.
DISCOVER_DEFINITION_TOPIC = '{}.discover.definition'.format(_BASE_)
#: Discover plugin topic event, used to discover the plugins.
DISCOVER_PLUGIN_TOPIC = '{}.discover.plugin'.format(_BASE_)
#: Discover widget topic event, used to discover the widgets of specific UI type.
DISCOVER_WIDGET_TOPIC = '{}.discover.widget'.format(_BASE_)
#: Discover engine topic event, used to discover the engines.
DISCOVER_ENGINE_TOPIC = '{}.discover.engine'.format(_BASE_)
#: Discover host topic event, used to discover available hosts.
DISCOVER_HOST_TOPIC = '{}.host.discover.host'.format(_BASE_)
#: Pipeline host run plugin topic event, used to communicate between client and
#: host, by the host connection to make the host run the plugin.
HOST_RUN_DEFINITION_TOPIC = '{}.host.run.definition'.format(_BASE_)
#: Run plugin topic event used to tell host from the client to run plugin.
HOST_RUN_PLUGIN_TOPIC = '{}.host.run.plugin'.format(_BASE_)
#: Execute plugin topic event used from the engine to tell the plugin to run.
EXECUTE_PLUGIN_TOPIC = '{}.execute.plugin'.format(_BASE_)
#: Plugin progres notification topic event, used to communicate the result of
#: the plugin execution from the plugin to the host.
NOTIFY_PLUGIN_PROGRESS_TOPIC = '{}.notify.plugin.progress'.format(_BASE_)
#: Pipeline client progress notification topic event, used to communicate the result of
#: the steps execution from host to the client.
NOTIFY_DEFINITION_PROGRESS_TOPIC = '{}.notify.definition.progress'.format(
    _BASE_
)
# Launch a widget within a client
CLIENT_LAUNCH_TOOL_TOPIC = '{}.client.launch.tool'.format(_BASE_)
# The main host context has changed, sent from host or host connection (change context)
HOST_CONTEXT_CHANGED_TOPIC = '{}.host.context.change'.format(_BASE_)
# The host connection context has changed, sent from host connection to clients
CLIENT_CONTEXT_CHANGED_TOPIC = '{}.client.context.change'.format(_BASE_)
# Host has added a new log item
HOST_LOG_ITEM_ADDED_TOPIC = '{}.host.log.added'.format(_BASE_)
# Client signal context changed
CLIENT_SIGNAL_CONTEXT_CHANGED_TOPIC = '{}.client.signal.context.change'.format(
    _BASE_
)
# Client signal host discovered
CLIENT_SIGNAL_HOSTS_DISCOVERED_TOPIC = '{}.client.signal.host.discover'.format(
    _BASE_
)
# Client signal host changed
CLIENT_SIGNAL_HOST_CHANGED_TOPIC = '{}.client.signal.host.change'.format(
    _BASE_
)
# Client signal definition changed
CLIENT_SIGNAL_DEFINITION_CHANGED_TOPIC = (
    '{}.client.signal.definition.change'.format(_BASE_)
)
# Client received plugin result
CLIENT_NOTIFY_RUN_PLUGIN_RESULT_TOPIC = (
    '{}.client.notify.plugin.result'.format(_BASE_)
)
# Client received definition result
CLIENT_NOTIFY_RUN_DEFINITION_RESULT_TOPIC = (
    '{}.client.notify.definition.result'.format(_BASE_)
)
# Client received log item result
CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC = '{}.client.notify.log_item'.format(_BASE_)
