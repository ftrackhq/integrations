# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import time
import logging
import uuid
from collections import defaultdict
from functools import partial
import atexit

from six import string_types

import ftrack_api

from ftrack_framework_core.widget.dialog import FrameworkDialog
import ftrack_constants.framework as constants

from ftrack_framework_core.client.host_connection import HostConnection

from ftrack_utils.decorators import track_framework_usage

from ftrack_utils.framework.config.tool import get_tool_config_by_name

from ftrack_framework_core.event import _EventHubThread
from ftrack_framework_core.client.utils import run_in_main_thread


class Client(object):
    '''
    Base client class.
    '''

    _static_properties = {}

    # tODO: evaluate if to use compatible UI types in here or directly add the list of ui types
    ui_types = constants.client.COMPATIBLE_UI_TYPES
    '''Compatible UI for this client.'''

    # TODO: Double check with the team if this is needed to have a singleton host
    #  connection and if it still makes sense to be a singleton as we only have
    #  one client now.
    _host_connection = None
    '''The singleton host connection used by all clients within the process space / DCC'''

    def __repr__(self):
        return '<Client:{0}>'.format(self.id)

    @property
    def id(self):
        '''Returns the current client id.'''
        return self._id

    @property
    def event_manager(self):
        '''Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`'''
        return self._event_manager

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    # TODO: Discuss if we want to change this to connected host
    @property
    def host_connection(self):
        '''
        Return instance of
        :class:`~ftrack_framework_core.client.HostConnection`
        '''
        return Client._host_connection

    @host_connection.setter
    def host_connection(self, value):
        '''
        Assign the host_connection to the given *value*

        *value* : should be instance of
        :class:`~ftrack_framework_core.client.HostConnection`
        '''
        if not value:
            # Clean up host_context_change_subscription in case exists
            self._unsubscribe_host_context_changed()
            Client._host_connection = value
            self.on_host_changed(self.host_connection)
            return
        if (
            self.host_connection
            and value.host_id == self.host_connection.host_id
        ):
            return

        self.logger.debug('Setting new host connection: {}'.format(value))
        Client._host_connection = value

        # Subscribe log item added
        self.event_manager.subscribe.host_log_item_added(
            self.host_connection.host_id,
            callback=self.on_log_item_added_callback,
        )
        # TODO: should this event go directly to dialog or widget and never
        #  pass through client?
        self.event_manager.subscribe.host_run_ui_hook_result(
            self.host_connection.host_id,
            callback=self.on_ui_hook_callback,
        )
        # Clean up host_context_change_subscription in case exists
        self._unsubscribe_host_context_changed()
        # Subscribe to host_context_change even though we already subscribed in
        # the host_connection. This is because we want to let the client know
        # that host changed context but also update the host connection to the
        # new context.
        self._host_context_changed_subscribe_id = (
            self.event_manager.subscribe.host_context_changed(
                self.host_connection.host_id,
                self._host_context_changed_callback,
            )
        )
        # Feed change of host and context to client
        self.on_host_changed(self.host_connection)
        self.on_context_changed(self.host_connection.context_id)

    @property
    def host_id(self):
        '''returns the host id from the current host connection'''
        if self.host_connection is None:
            raise Exception('No host connection available')
        return self.host_connection.host_id

    @property
    def context_id(self):
        '''Returns the current context id from current host connection'''
        if not self.host_connection:
            self.logger.warning('No host connection available')
            return
        return self.host_connection.context_id

    @context_id.setter
    def context_id(self, context_id):
        '''Publish the given *context_id to be set by the host'''
        if not isinstance(context_id, string_types):
            raise ValueError('Context should be in form of a string.')
        if self.host_connection is None:
            raise Exception('No host connection available')
        # Publish event to notify host that client has changed the context
        self.event_manager.publish.client_context_changed(
            self.host_id, context_id
        )

    @property
    def host_context_changed_subscribe_id(self):
        '''The subscription id of the host context changed event'''
        return self._host_context_changed_subscribe_id

    @property
    def tool_configs(self):
        '''Returns all available tool_configs from the current host_ connection'''
        if not self.host_connection:
            raise Exception('No host connection available')
        return self.host_connection.tool_configs

    # Widget
    @property
    def dialogs(self):
        '''Return instanced dialogs'''
        return self.__instanced_dialogs

    @property
    def dialog(self):
        '''Return the current active dialog'''
        return self._dialog

    @dialog.setter
    def dialog(self, value):
        # TODO: Check value is type of framework dialog
        '''Set the given *value* as the current active dialog'''
        self.set_active_dialog(self._dialog, value)
        self._dialog = value

    @property
    def registry(self):
        '''Return registry object'''
        return self._registry

    @property
    def tool_config_options(self):
        return self._tool_config_options

    @property
    def remote_session(self):
        # TODO: temporary hack for remote session
        if self._remote_session:
            return self._remote_session
        else:
            self._remote_session = ftrack_api.Session(
                auto_connect_event_hub=True
            )
            # TODO: temporary solution to start the wait thread
            self._event_hub_thread = _EventHubThread(self._remote_session)

            if not self._event_hub_thread.is_alive():
                self.logger.debug(
                    'Starting new hub thread for {}'.format(self)
                )
                self._event_hub_thread.start()

                # Make sure it is shutdown
                atexit.register(self.close)

            return self._remote_session

    def __init__(
        self, event_manager, registry, run_in_main_thread_wrapper=None
    ):
        '''
        Initialise Client with instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        # TODO: double check logger initialization and standardize it around all files.
        # Setting logger
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # Create the client id to use to communicate with UI
        self._id = '{}'.format(uuid.uuid4().hex)

        # Set the event manager
        self._event_manager = event_manager

        # Setting init variables to 0
        self._registry = registry
        self._host_context_changed_subscribe_id = None
        self.__instanced_dialogs = {}
        self._dialog = None
        self._tool_config_options = defaultdict(defaultdict)
        self._remote_session = None
        self._event_hub_thread = None

        # Set up the run_in_main_thread decorator
        self.run_in_main_thread_wrapper = run_in_main_thread_wrapper
        Client._static_properties[
            'run_in_main_thread_wrapper'
        ] = self.run_in_main_thread_wrapper

        self.logger.debug('Initialising Client {}'.format(self))

        self.discover_host()

    @staticmethod
    def static_properties():
        '''Return the singleton instance.'''
        return Client._static_properties

    # Host
    def discover_host(self, time_out=3):
        '''
        Find for available hosts during the optional *time_out*.

        This removes all previously discovered host connections.
        '''
        # Reset host connections
        if self.host_connection:
            self._unsubscribe_host_context_changed()
            self.host_connection = None

        # discovery host loop and timeout.
        start_time = time.time()
        self.logger.debug('time out set to {}:'.format(time_out))
        if not time_out:
            self.logger.warning(
                'Running client with no time out.'
                'Will not stop until discover a host.'
                'Terminate with: Ctrl-C'
            )

        while not self.host_connection:
            delta_time = time.time() - start_time

            if time_out and delta_time >= time_out:
                self.logger.warning('Could not discover any host.')
                break

            self.event_manager.publish.discover_host(
                callback=self._host_discovered_callback
            )

    @track_framework_usage('FRAMEWORK_HOST_DISCOVERED', {'module': 'client'})
    def _host_discovered_callback(self, event):
        '''
        Reply callback of the discover host event, generate
        :class:`~ftrack_framework_core.client.HostConnection`
        of all discovered hosts from the given *event*.

        *event*: :class:`ftrack_api.event.base.Event`
        '''
        if not event['data']:
            return
        for reply_data in event['data']:
            self.host_connection = HostConnection(
                self.event_manager, reply_data
            )
            break

    def on_host_changed(self, host_connection):
        '''Called when the host has been (re-)selected by the user.'''
        # Emit signal to widget
        self.event_manager.publish.client_signal_host_changed(self.id)

    # Context
    @run_in_main_thread
    def _host_context_changed_callback(self, event):
        '''Set the new context ID based on data provided in *event*'''
        # Feed the new context to the client
        self.on_context_changed(event['data']['context_id'])

    def on_context_changed(self, context_id):
        '''Called when the context has been set or changed within the
        host connection, either from this client or remote
        (other client or the host).
        '''
        # Emit signal to widget
        self.event_manager.publish.client_signal_context_changed(self.id)

    def _unsubscribe_host_context_changed(self):
        '''Unsubscribe to client context change events'''
        if self.host_context_changed_subscribe_id:
            self.event_manager.unsubscribe(
                self.host_context_changed_subscribe_id
            )
            self._host_context_changed_subscribe_id = None

    # Tool config
    def run_tool_config(self, tool_config_reference):
        '''
        Publish event to tell the host to run the given *tool_config_reference*
        on the engine.
        *tool_config_reference*: id number of the tool config.
        '''
        self.event_manager.publish.host_run_tool_config(
            self.host_id,
            tool_config_reference,
            self.tool_config_options.get(tool_config_reference, {}),
        )

    # Plugin
    @run_in_main_thread
    def on_log_item_added_callback(self, event):
        '''
        Called when a log item has added in the host.
        '''
        log_item = event['data']['log_item']
        self.logger.info(
            f"Plugin Execution progress: \n "
            f"name: {log_item.name} \n"
            f"status: {log_item.status} \n"
            f"message: {log_item.message} \n"
            f"execution_time: {log_item.execution_time} \n"
            f"options: {log_item.options} \n"
            f"store: {log_item.store} \n"
        )
        # Publish event to widget
        self.event_manager.publish.client_notify_log_item_added(
            self.id, event['data']['log_item']
        )

    @run_in_main_thread
    def on_ui_hook_callback(self, event):
        '''
        Called ui_hook has been executed on host and needs to notify UI with
        the result.
        '''
        # Publish event to widget
        self.event_manager.publish.client_notify_ui_hook_result(
            self.id,
            event['data']['plugin_reference'],
            event['data']['ui_hook_result'],
        )

    def reset_all_tool_configs(self):
        '''
        Ask host connection to reset values of all tool_configs
        '''
        self.host_connection.reset_all_tool_configs()

    @run_in_main_thread
    def _on_discover_action_callback(self, name, dialog_name, options, event):
        '''Discover *event*.'''
        self.logger.warning(
            f"on discover action: {name} {dialog_name} {options} {event}"
        )
        '''
        on discover action: loader framework_standard_opener_dialog {'tool_configs': ['maya-scene-opener']} <Event {'id': '2eaf07ae868d4ab8965aebd1121c4e01', 'data': {'selection': [{'entityId': 'fe0b1b3e-0788-4a62-b6be-537f0253c244', 'entityType': 'Component'}], 'groupers': [], 'filters': [], 'sorters': [{'direction': 'ASC', 'property': 'label', 'root': 'data'}]}, 'topic': 'ftrack.action.discover', 'sent': None, 'source': {'clientToken': '0e1e50b7-deb6-43f2-9273-c2d7b3e970b0-1718089829679', 'id': '7e4c3980021043ed81e9c06a7e0d60b8', 'user': {'username': 'lluis.casals@ftrack.com', 'id': '7e27761c-a36d-11ec-a671-3af9d77ae1b2'}}, 'target': '', 'in_reply_to_event': None}> // 

        '''
        selection = event['data'].get('selection', [])
        if len(selection) == 1 and selection[0]['entityType'] == 'Component':
            return {
                'items': [
                    {
                        'label': name,
                        #'actionIdentifier': self.identifier,
                        'host_id': self.host_id,
                        'dialog_name': dialog_name,
                        'options': options,
                    }
                ]
            }

    @run_in_main_thread
    def _on_launch_action_callback(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        '''
        <Event {'id': '2e7337fd214741a398050d01ddf691c2', 'data': {'selection': [{'entityId': 'fe0b1b3e-0788-4a62-b6be-537f0253c244', 'entityType': 'Component'}], 'dialog_name': 'framework_standard_opener_dialog', 'label': 'loader', 'options': {'tool_configs': ['maya-scene-opener']}, 'host_id': 'e7864dad03ba4f19b069a3b99fb3307c'}, 'topic': 'ftrack.action.launch', 'sent': None, 'source': {'clientToken': '0e1e50b7-deb6-43f2-9273-c2d7b3e970b0-1718089829679', 'id': '7e4c3980021043ed81e9c06a7e0d60b8', 'user': {'username': 'lluis.casals@ftrack.com', 'id': '7e27761c-a36d-11ec-a671-3af9d77ae1b2'}}, 'target': '', 'in_reply_to_event': None}> // 
        <Event {'id': '2e7337fd214741a398050d01ddf691c2', 'data': {'selection': [{'entityId': 'fe0b1b3e-0788-4a62-b6be-537f0253c244', 'entityType': 'Component'}], 'dialog_name': 'framework_standard_opener_dialog', 'label': 'loader', 'options': {'tool_configs': ['maya-scene-opener']}, 'host_id': 'e7864dad03ba4f19b069a3b99fb3307c'}, 'topic': 'ftrack.action.launch', 'sent': None, 'source': {'clientToken': '0e1e50b7-deb6-43f2-9273-c2d7b3e970b0-1718089829679', 'id': '7e4c3980021043ed81e9c06a7e0d60b8', 'user': {'username': 'lluis.casals@ftrack.com', 'id': '7e27761c-a36d-11ec-a671-3af9d77ae1b2'}}, 'target': '', 'in_reply_to_event': None}> // 

        '''
        self.logger.warning(f"on _on_launch_action_callback: {event}")
        selection = event['data']['selection']

        name = event['data']['label']
        dialog_name = event['data']['dialog_name']
        options = event['data']['options']
        options['event_data'] = {'selection': selection}

        self.run_tool(name, None, dialog_name, options)

    def _print_all(self, event):
        self.logger.warning(f"all event: {event}")

    @track_framework_usage(
        'FRAMEWORK_RUN_TOOL',
        {'module': 'client'},
        ['name'],
    )
    def run_tool(
        self,
        name,
        run_on=None,
        dialog_name=None,
        options=dict,
        dock_func=False,
    ):
        '''
        Client runs the tool passed from the DCC config, can run run_dialog
        if the tool has UI or directly run_tool_config if it doesn't.
        '''

        self.logger.info(f"Running {name} tool")
        self.logger.warning(
            f"on run_tool: "
            f"{name} {run_on} {dialog_name} {options} {dock_func}"
        )
        self.remote_session.event_hub.subscribe(
            u'topic=ftrack.*', self._print_all
        )
        '''
        on run_tool: loader action framework_standard_opener_dialog {'tool_configs': ['maya-scene-opener']} <function dock_maya_right at 0x7f8d817ea050> # 

        '''

        if run_on == 'action':
            # TODO: we don't support dock_fn in here because is not serializable
            self.logger.warning("run on action")

            self.remote_session.event_hub.subscribe(
                u'topic=ftrack.action.discover and '
                u'source.user.username="{0}"'.format(self.session.api_user),
                partial(
                    self._on_discover_action_callback,
                    name,
                    dialog_name,
                    options,
                ),
            )

            self.remote_session.event_hub.subscribe(
                u'topic=ftrack.action.launch and '
                # u'data.actionIdentifier={0} and '
                u'data.label={0} and '
                u'source.user.username="{1}" and '
                u'data.host_id={2}'.format(
                    name, self.session.api_user, self.host_id
                ),
                self._on_launch_action_callback,
            )
            # subscribe to ftrack.action.discover event and pass the label of the action
            # subscribe to ftrack.action.launch event and pass the dialog_name, tool_configs, etc to run the run_tool...

            return

        # TODO: if run_on is not action, simply continue and execute the tool

        if dialog_name:
            self.run_dialog(
                dialog_name,
                dialog_options=options,
                dock_func=dock_func,
            )
        else:
            # TODO: temporal hack solution to get all self.tool_configs on a plain list.
            tool_configs = [
                config
                for sublist in self.tool_configs.values()
                for config in sublist
            ]
            for tool_config_name in options.get('tool_configs'):
                tool_config = get_tool_config_by_name(
                    tool_configs, tool_config_name
                )
                if not tool_config:
                    self.logger.error(
                        f"Couldn't find any tool config matching the name {tool_config_name}"
                    )
                    continue

                self.set_config_options(
                    tool_config['reference'], options=options
                )

                self.run_tool_config(tool_config['reference'])

    # UI
    @track_framework_usage(
        'FRAMEWORK_RUN_DIALOG',
        {'module': 'client'},
        ['dialog_name', 'dialog_options'],
    )
    def run_dialog(
        self,
        dialog_name,
        dialog_class=None,
        dialog_options=None,
        dock_func=None,
    ):
        '''Function to show a framework dialog by name *dialog_name* from the
        client, using *dialog_class* or picking class from registry. Passes on
        *dialog_options* to the dialog.
        *dock_func* is an optional function to dock the dialog in a way for a specific DCC
        '''

        # use dialog options to pass options to the dialog like for
        #  example: Dialog= WidgetDialog dialog_options= {tool_config_plugin: Context_selector}
        #  ---> So this will execute the widget dialog with the widget of the
        #  context_selector in it, it simulates a run_widget).
        #  Or any other kind of option like docked or not

        if dialog_class:
            if not isinstance(dialog_class, FrameworkDialog):
                error_message = (
                    'The provided class {} is not instance of the base framework '
                    'widget. Please provide a supported widget.'.format(
                        dialog_class
                    )
                )
                self.logger.error(error_message)
                raise Exception(error_message)

            if dialog_class not in [
                dialog['extension'] for dialog in self.registry.dialogs
            ]:
                self.logger.warning(
                    'Provided dialog_class {} not in the discovered framework '
                    'widgets, registering...'.format(dialog_class)
                )
                self.registry.add(
                    extension_type='dialog',
                    name=dialog_name,
                    extension=dialog_class,
                )

        if dialog_name and not dialog_class:
            for registered_dialog_class in self.registry.dialogs:
                if dialog_name == registered_dialog_class['name']:
                    dialog_class = registered_dialog_class['extension']
                    break
        if not dialog_class:
            error_message = (
                'Please provide a registered dialog name.\n'
                'Given name: {} \n'
                'registered widgets: {}'.format(
                    dialog_name, self.registry.dialogs
                )
            )
            self.logger.error(error_message)
            raise Exception(error_message)

        dialog = dialog_class(
            self.event_manager,
            self.id,
            connect_methods_callback=self._connect_methods_callback,
            connect_setter_property_callback=self._connect_setter_property_callback,
            connect_getter_property_callback=self._connect_getter_property_callback,
            dialog_options=dialog_options,
        )
        # Append dialog to dialogs
        self._register_dialog(dialog)
        self.dialog = dialog
        # If a docking function is provided, use it
        if dialog_options.get('docked') and dock_func:
            dock_func(self.dialog)
        else:
            self.dialog.show_ui()
            self.dialog.setFocus()

    def _register_dialog(self, dialog):
        '''Register the given initialized *dialog* to the dialogs registry'''
        if dialog.id not in list(self.__instanced_dialogs.keys()):
            self.__instanced_dialogs[dialog.id] = dialog

    def set_active_dialog(self, old_dialog, new_dialog):
        '''Remove focus from the *old_dialog* and set the *new_dialog*'''
        for dialog in list(self.dialogs.values()):
            dialog.change_focus(old_dialog, new_dialog)

    def _connect_methods_callback(
        self, method_name, arguments=None, callback=None
    ):
        '''
        Callback from the dialog to execute the given *method_name* from the
        client with the given *arguments* call the given *callback* once we have
        the result
        '''
        meth = getattr(self, method_name)
        if not arguments:
            arguments = {}
        result = meth(**arguments)
        if callback:
            callback(result)
        return result

    def _connect_setter_property_callback(self, property_name, value):
        '''
        Callback from the dialog, set the given *property_name* from the
        client to the given *value*
        '''
        self.__setattr__(property_name, value)

    def _connect_getter_property_callback(self, property_name):
        '''
        Callback from the dialog, return the value of the given *property_name*
        '''
        return self.__getattribute__(property_name)

    def set_config_options(
        self, tool_config_reference, plugin_config_reference=None, options=None
    ):
        self.logger.warning(
            f"set_config_options --> {tool_config_reference}, {plugin_config_reference}, {options}"
        )
        if not options:
            options = dict()
        # TODO_ mayabe we should rename this one to make sure this is just for plugins
        if not isinstance(options, dict):
            raise Exception(
                "plugin_options should be a dictionary. "
                "Current given type: {}".format(options)
            )
        if not plugin_config_reference:
            self._tool_config_options[tool_config_reference][
                'options'
            ] = options
        else:
            self._tool_config_options[tool_config_reference][
                plugin_config_reference
            ] = options

    def run_ui_hook(
        self, tool_config_reference, plugin_config_reference, payload
    ):
        '''
        Publish event to tell the host to run the given *tool_config_reference*
        on the engine.
        *tool_config_reference*: id number of the tool config.
        *plugin_config_reference*: id number of the plugin config.
        *payload*: dictionary of data to send to the plugin.
        '''
        self.event_manager.publish.host_run_ui_hook(
            self.host_id,
            tool_config_reference,
            plugin_config_reference,
            self.tool_config_options[tool_config_reference].get(
                plugin_config_reference, {}
            ),
            payload,
        )

    def verify_plugins(self, plugin_names):
        '''
        Verify if the given *plugins* are registered in the host registry.
        '''
        unregistered_plugins = self.event_manager.publish.host_verify_plugins(
            self.host_id, plugin_names
        )[0]
        return unregistered_plugins

    def close(self):
        self.logger.debug('Shutting down client')
        if (
            self._remote_session
            and self._event_hub_thread
            and self._event_hub_thread.is_alive()
        ):
            self.logger.debug('Stopping event hub thread')
            self._event_hub_thread.stop()
            self._event_hub_thread = None
            self._remote_session.close()
            self._remote_session = None
