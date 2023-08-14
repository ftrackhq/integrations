# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import functools
import logging
import ftrack_api
import time
import uuid
# TODO: move plugin constants to plugin repo
#  Also create STTUS LIST
from ftrack_framework_plugin import constants
# TODO: double check if we really need the ftrackobject manager and the dcc, in case we need it, d
from ftrack_framework_plugin import validation

# TODO: We will not have the plugins separated, all them will inherit from the
#  basePlugin and will pass the type, we will only check if the type is valid.
#  Overrides will be exposed in the core_plugins library.
# TODO: also the plugins will have the attribute widget, that the user can override but we will not have the widget type of plugin.
class BasePlugin(object):
    '''Base Class to represent a Plugin'''

    # We Define name, plugin_type and host_type as class variables for
    # convenience for the user when creating its own plugin.
    name = None
    plugin_type = None
    host_type = None

    def __repr__(self):
        return '<{}:{}>'.format(self.plugin_type, self.name)

    # TODO: double check when we really need this.
    @property
    def ftrack_object_manager(self):
        '''
        Initializes and returns an instance of
        :class:`~ftrack_framework_core.asset.FtrackObjectManager`
        '''
        return self._ftrack_object_manager

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self.event_manager.session

    @property
    def event_manager(self):
        '''
        Returns instance of
        :class:`~ftrack_framework_core.event.EventManager`
        '''
        return self._event_manager

    @property
    def id(self):
        '''
        Id of the plugin
        '''
        return self._id

    @property
    def host_id(self):
        '''
        Type of the plugin
        '''
        return self._host_id

    @property
    def method_result(self):
        '''
        Type of the plugin
        '''
        return self._method_result

    @method_result.setter
    def method_result(self, value):
        '''
        Type of the plugin
        '''
        is_valid = self._validate_result(value)
        if not is_valid:
            self.status = constants.status.EXCEPTION_STATUS

        self._method_result = value
        self.result_registry = value

    @property
    def result_registry(self):
        '''
        Type of the plugin
        '''
        return self._result_registry

    @result_registry.setter
    def result_registry(self, value):
        '''
        Type of the plugin
        '''
        self._result_registry[self.method] = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in constants.status.STATUS_LIST:
            self.logger.error(
                "Status {} is not recognized. Available statuses are: {}".format(
                    value, constants.status.STATUS_LIST
                )
            )
            value = constants.status.EXCEPTION_STATUS
        self._status = value

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value

    @property
    def boolean_status(self):
        return constants.status.status_bool_mapping[self.status]

    @property
    def execution_time(self):
        return self._execution_time

    @execution_time.setter
    def execution_time(self, value):
        self._execution_time = value

    # TODO: is this used?
    @property
    def raw_plugin_data(self):
        # TODO: fix this docstring
        '''Returns the current context id'''
        return self._raw_plugin_data

    @property
    def method(self):
        '''Returns the method of the plugin that will be executed'''
        return self._method

    @property
    def default_method(self):
        '''Returns the default executable methodof the plugin'''
        return self._default_method

    @property
    def methods(self):
        '''List all available executable methods'''
        return self._methods

    @property
    def context_data(self):
        '''List all available executable methods'''
        return self._context_data

    @property
    def plugin_data(self):
        '''List all available executable methods'''
        return self._plugin_data

    @property
    def plugin_options(self):
        '''List all available executable methods'''
        return self._plugin_options

    @property
    def plugin_widget_id(self):
        '''List all available executable methods'''
        return self._plugin_widget_id

    @property
    def plugin_widget_name(self):
        '''List all available executable methods'''
        return self._plugin_widget_name

    # TODO: should we pass the host itself instead of the event_manager? so if
    #  user wants, he can query stuff from core using host, like:
    #  host.constants.asset_Name
    def __init__(self, event_manager, host_id, ftrack_object_manager):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._event_manager = event_manager
        self._ftrack_object_manager = ftrack_object_manager
        self._host_id = host_id
        self._id = uuid.uuid4().hex
        self._raw_plugin_data = []
        self._methods = {}
        self._status = constants.status.UNKNOWN_STATUS
        self._message = ''
        self._method = None
        self._default_method = None
        self._execution_time = 0
        self._result_registry = {}
        self._method_result = None
        self._plugin_widget_id = None
        self._plugin_widget_name = None

        self.register_methods()

    # TODO: make this ABC
    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value={'asd':'asd'}
        )

    def register_method(
            self, method_name, required_output_type, required_output_value
    ):
        self._methods[method_name] = {
            'required_output_type': required_output_type,
            'required_output_value': required_output_value
        }

    # TODO: This should be ABC
    def pre_execute_callback_hook(self, event):
        return event

    def _execute_callback(self, event):
        start_time = time.time()

        #Reset all statuses
        self.status = constants.status.DEFAULT_STATUS
        self.message = None
        self._method_result = None

        # Override the current execute method for the one given by the event
        self._default_method = event['data'].get('plugin_default_method')
        self._method = event['data'].get('plugin_method')
        self._context_data = event['data'].get('plugin_context_data')
        self._plugin_data = event['data'].get('plugin_data')
        self._plugin_options = event['data'].get('plugin_options')
        self._plugin_widget_id = event['data'].get('plugin_widget_id')
        self._plugin_widget_name = event['data'].get('plugin_widget_name')

        # Pre execute callback hook
        self.message = "Execute pre_execute_callback"
        self._notify_client()
        # reset message
        self.message = None
        try:
            self.status = constants.status.RUNNING_STATUS
            event = self.pre_execute_callback_hook(event)
        except Exception as e:
            # If status is valid, set to not
            if self.boolean_status:
                self._status = constants.status.EXCEPTION_STATUS
            # If status is already handled by the plugin we check if message is
            # also handled if not set a generic one
            if not self.message:
                self.message = (
                    "Error executing pre_execute_callback_hook: {} \n "
                    "status {}".format(
                    e, self.status
                    )
                )
            # If booth handled by the plugin, logger the message
            self.logger.error(self.message)
            self._notify_client()
            return self.provide_plugin_info()

        # Print post Execute error handled by the plugin
        if not self.boolean_status:
            # Generic message printing the result in case no message is provided.
            if not self.message:
                self.message = (
                    "Error detected on the pre execute funtion of the plugin {}, "
                    "but no message provided. "
                    "event is: {}.".format(self.name, event)
                )
            self.logger.error(self.message)
            self._notify_client()
            return self.provide_plugin_info()

        # Get the execute Method
        execute_fn = getattr(self, self.method)

        self.message = (
            "Execute method {} with following arguments:\n "
            "context_data: {} \n "
            "data: {} \n "
            "options: {}".format(
                self.method, self.context_data, self.plugin_data, self.plugin_options
            )
        )
        self.status = constants.status.RUNNING_STATUS
        self._notify_client()
        # reset message
        self.message = None

        try:
            # Execute the method
            # TODO: maybe here in the future we can pass different arguments, but
            #  think about it carefully, because this might make it over complicated.
            self.method_result = execute_fn(
                context_data=self.context_data,
                data=self.plugin_data,
                options=self.plugin_options
            )
        except Exception as e:
            if self.boolean_status:
                self._status = constants.status.EXCEPTION_STATUS
            # If status is already handled by the plugin we check if message is
            # also handled if not set a generic one
            if not self.message:
                self.message = "Error executing plugin {} status {}".format(
                    e, self.status
                )
            # If booth handled by the plugin, logger the message
            self.logger.error(self.message)
            self._notify_client()
            return self.provide_plugin_info()

        # print plugin error handled by the plugin
        if not self.boolean_status:
            # Generic message printing the result in case no message is provided.
            if not self.message:
                self.message = (
                    "Error detected on the plugin {}, but no message provided. "
                    "Result is {}.".format(self.name, self.method_result)
                )
            self.logger.error(self.message)
            self._notify_client()
            return self.provide_plugin_info()

        # Notify client
        self.message = "Plugin executed succesfully, result: {}".format(
            self.method_result
        )
        self._notify_client()
        # Post execute callback hook
        # reset message
        self.message = None
        try:
            # We are not setting the post_execute_result as the result for now
            # because is a free method that maight not validate.
            post_execute_result = self.post_execute_callback_hook(
                self.method_result
            )
        except Exception as e:
            # If status is valid, set to not
            if self.boolean_status:
                self._status = constants.status.EXCEPTION_STATUS
            # If status is already handled by the plugin we check if message is
            # also handled if not set a generic one
            if not self.message:
                self.message = (
                    "Error executing post_execute_callback_hook: {} \n "
                    "status {}".format(
                    e, self.status
                    )
                )
            # If booth handled by the plugin, logger the message
            self.logger.error(self.message)
            self._notify_client()
            return self.provide_plugin_info()

        # Print post Execute error handled by the plugin
        if not self.boolean_status:
            # Generic message printing the result in case no message is provided.
            if not self.message:
                self.message = (
                    "Error detected on the post execute funtion of the plugin {}, "
                    "but no message provided. "
                    "Result is: {}.".format(self.name, post_execute_result)
                )
            self.logger.error(self.message)
            self._notify_client()
            return self.provide_plugin_info()

        self.message = "Post execute plugin succesfully, result: {}".format(
            post_execute_result
        )
        self.status = constants.status.SUCCESS_STATUS
        end_time = time.time()
        total_time = end_time - start_time
        self.execution_time = total_time

        self._notify_client()
        return self.provide_plugin_info()

    # TODO: This should be ABC
    def post_execute_callback_hook(self, result):
        return result

    def provide_plugin_info(self):
        return {
            'host_id': self.host_id,
            'plugin_name': self.name,
            'plugin_type': self.plugin_type,
            'plugin_id': self.id,
            'plugin_method': self.method,
            'host_type': self.host_type,
            'plugin_boolean_status': self.boolean_status,
            'plugin_status': self.status,
            'plugin_method_result': self.method_result,
            'plugin_result_registry': self.result_registry,
            'plugin_execution_time': self.execution_time,
            'plugin_message': self.message,
            'plugin_context_data':self.context_data,
            'plugin_data': self.plugin_data,
            'plugin_options': self.plugin_options,
            'plugin_widget_id': self.plugin_widget_id,
            'plugin_widget_name': self.plugin_widget_name,
        }

    def register(self):
        '''
        Register function of the plugin to regiter it self.

        .. note::

            This function subscribes the plugin to two
            :class:`ftrack_api.event.base.Event` topics:

            :const:`~ftrack_framework_core.constants.DISCOVER_PLUGIN_TOPIC`:
            Topic to make the plugin discoverable for the host.

            :const:`~ftrack_framework_core.constants.HOST_RUN_PLUGIN_TOPIC`:
            Topic to execute the plugin
        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        self.logger.debug(
            'registering: {} for {}'.format(self.name, self.plugin_type)
        )

        # TODO: move the subscriptions to a standar subscription method?
        self.event_manager.subscribe.execute_plugin(
            self.host_type,
            self.name,
            callback=self._execute_callback
        )

        # subscribe to discover the plugin
        self.event_manager.subscribe.discover_plugin(
            self.host_type,
            self.name,
            callback=self._discover_callback
        )

    def _discover_callback(self, event):
        '''
        Callback of
        :const:`~ftrack_framework_core.constants.DISCOVER_PLUGIN_TOPIC`
        Makes sure the plugin is discoverable for the host.

        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return False

        return True

    def _validate_result(self, result):
        '''
        Validates the *result* of the :meth:`run` of the plugin using the
        :obj:`validator` and the :meth:`validator.validate_result_type`,
        :meth:`validator.validate_required_output`,
        :meth:`validator.validate_result_value`

        Returns a status and string message
        '''
        is_valid = validation.validate_output_type(
            type(result),
            self.methods[self.method].get('required_output_type')
        )
        if not is_valid:
            self.message = (
                'Plugin result type, does not match required output type \n '
                'Result type: {} \n '
                'Required type: {}'.format(
                    type(result),
                    self.methods[self.method].get('required_output_type')
                )
            )
            return is_valid

        if self.methods[self.method].get('required_output_value'):
            is_valid = validation.validate_output_value(
                result,
                self.methods[self.method].get('required_output_value')
            )
            if not is_valid:
                self.message = (
                    'Plugin result, does not match required output value \n '
                    'Result: {} \n '
                    'Required output: {}'.format(
                        result,
                        self.methods[self.method].get('required_output_value')
                    )
                )
        return is_valid

    # This is the previous _parse_run_event, but cleaned up
    def get_previous_stage_data(self, plugin_data, stage_name):
        '''
        Parse plugin_data to return only the previous given stage_name data
        '''
        collector_result = []
        component_step = plugin_data[-1]
        for component_stage in component_step.get("result"):
            if component_stage.get("name") == stage_name:
                collector_result = component_stage.get("result")
                break
        return collector_result

    # TODO: this should be an ABC method
    def run(self, context_data=None, data=None, options=None):
        '''
        Runs the current plugin with , *context_data* , *data* and *options*.

        *context_data* provides a mapping with the asset_name, context_id, asset_type_name,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector or empty list

        *options* a dictionary of options passed from outside.

        .. note::

            Use always self.exporters as a base to return the values,
            don't override self.exporters as it contains the _required_output

        '''
        raise NotImplementedError('Missing run method.')

    # TODO: this should be an ABC method
    def fetch(self, context_data=None, data=None, options=None):
        '''
        Runs the current plugin with , *context_data* , *data* and *options*.


        *context_data* provides a mapping with the asset_name, context_id, asset_type_name,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector or empty list

        *options* a dictionary of options passed from outside.

        .. note::

            This function is meant to be ran as an alternative of the default run
            function. Usually to fetch information for the widget or to test the
            plugin.

        '''
        raise NotImplementedError('Missing fetch method.')

    def _notify_client(self):
        self.event_manager.publish.notify_plugin_progress_client(
            self.provide_plugin_info()
        )

