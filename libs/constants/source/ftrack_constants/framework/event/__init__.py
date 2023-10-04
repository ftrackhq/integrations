# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

#: Run the events of the session in remote mode
REMOTE_EVENT_MODE = 1
#: Run the events of the session in local mode
LOCAL_EVENT_MODE = 0

#: See event_table.md from :ref:`~framework_core.doc.developing.event_table.md` file for a
# better reference on each event.

#: Base name for events
_BASE_ = 'ftrack.framework'

#: Register tool config topic event.
DISCOVER_TOOL_CONFIG_TOPIC = '{}.discover.tool_config'.format(_BASE_)
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
HOST_RUN_TOOL_CONFIG_TOPIC = '{}.host.run.tool_config'.format(_BASE_)
#: Run plugin topic event used to tell host from the client to run plugin.
HOST_RUN_PLUGIN_TOPIC = '{}.host.run.plugin'.format(_BASE_)
#: Execute plugin topic event used from the engine to tell the plugin to run.
EXECUTE_PLUGIN_TOPIC = '{}.execute.plugin'.format(_BASE_)
#: Plugin progres notification topic event, used to communicate the result of
#: the plugin execution from the plugin to the host.
NOTIFY_PLUGIN_PROGRESS_TOPIC = '{}.notify.plugin.progress'.format(_BASE_)
#: Pipeline client progress notification topic event, used to communicate the result of
#: the steps execution from host to the client.
NOTIFY_TOOL_CONFIG_PROGRESS_TOPIC = '{}.notify.tool_config.progress'.format(
    _BASE_
)
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
# Client signal tool config changed
CLIENT_SIGNAL_TOOL_CONFIG_CHANGED_TOPIC = (
    '{}.client.signal.tool_config.change'.format(_BASE_)
)
# Client received plugin result
CLIENT_NOTIFY_RUN_PLUGIN_RESULT_TOPIC = (
    '{}.client.notify.plugin.result'.format(_BASE_)
)
# Client received tool config result
CLIENT_NOTIFY_RUN_TOOL_CONFIG_RESULT_TOPIC = (
    '{}.client.notify.tool_config.result'.format(_BASE_)
)
# Client received log item result
CLIENT_NOTIFY_LOG_ITEM_ADDED_TOPIC = '{}.client.notify.log_item'.format(_BASE_)


# Remote JS integration<>Python communication; Connection and alive check
REMOTE_ALIVE_TOPIC = "{}.remote.alive".format(_BASE_)

# Remote JS integration<>Python communication; Connection and alive check acknowledgement
REMOTE_ALIVE_ACK_TOPIC = "{}.remote.alive.ack".format(_BASE_)

# Remote JS integration<>Python communication; Context data
REMOTE_CONTEXT_DATA_TOPIC = "{}.remote.context.data".format(_BASE_)
