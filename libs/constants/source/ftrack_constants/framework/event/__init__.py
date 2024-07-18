# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

#: See event_table.md from :ref:`~framework_core.doc.developing.event_table.md` file for a
# better reference on each event.

#: Ftrack general events
FTRACK_ACTION_DISCOVER_TOPIC = 'ftrack.action.discover'
FTRACK_ACTION_LAUNCH_TOPIC = 'ftrack.action.launch'

#: Base name for events
_BASE_ = 'ftrack.framework'

#: Discover host topic event, used to discover available hosts.
DISCOVER_HOST_TOPIC = '{}.host.discover.host'.format(_BASE_)
#: Pipeline host run plugin topic event, used to communicate between client and
#: host, by the host connection to make the host run the plugin.
HOST_RUN_TOOL_CONFIG_TOPIC = '{}.host.run.tool_config'.format(_BASE_)
#: Run ui hook topic event used to tell host from the client to run the ui hook method of the plugin..
HOST_RUN_UI_HOOK_TOPIC = '{}.host.run.ui_hook'.format(_BASE_)
# The main host context has changed, sent from host or host connection (change context)
HOST_CONTEXT_CHANGED_TOPIC = '{}.host.context.change'.format(_BASE_)
# The host connection context has changed, sent from host connection to clients
CLIENT_CONTEXT_CHANGED_TOPIC = '{}.client.context.change'.format(_BASE_)
# Host has added a new log item
HOST_LOG_ITEM_ADDED_TOPIC = '{}.host.log.added'.format(_BASE_)
# Host has a new result from ui hook method.
HOST_UI_HOOK_RESULT_TOPIC = '{}.host.ui_hook.result'.format(_BASE_)
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
# Client received ui_hook result
CLIENT_NOTIFY_UI_HOOK_RESULT_TOPIC = '{}.client.notify.ui_hook_result'.format(
    _BASE_
)
# Client wants to verify the plugins are registered in host
HOST_VERIFY_PLUGINS_TOPIC = '{}.host.verify.plugins'.format(_BASE_)

# Remote integration<>Python communication; Connection and alive check
DISCOVER_REMOTE_INTEGRATION_TOPIC = "{}.discover.remote.integration".format(
    _BASE_
)

# Remote integration<>Python communication; Provide context data to JS
REMOTE_INTEGRATION_CONTEXT_DATA_TOPIC = (
    "{}.remote.integration.context.data".format(_BASE_)
)

# Remote integration<>Python communication; Launch tool
REMOTE_INTEGRATION_RUN_DIALOG_TOPIC = (
    "{}.remote.integration.run.dialog".format(_BASE_)
)

# Remote integration<>Python communication; Run JS function with arguments
REMOTE_INTEGRATION_RPC_TOPIC = "{}.remote.integration.rpc".format(_BASE_)
