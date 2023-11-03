# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging
import time
import uuid
from abc import ABC, abstractmethod

import ftrack_constants.framework as constants

from ftrack_framework_plugin import validation


# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))


class BasePlugin(ABC):
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
        host id
        '''
        return self._host_id

    @property
    def method_result(self):
        '''
        Result of the current method
        '''
        return self._method_result

    @method_result.setter
    def method_result(self, value):
        '''
        Set the result of the current method and registry it to the
        registrated results.
        '''
        is_valid = self._validate_result(value)
        if not is_valid:
            self.status = constants.status.EXCEPTION_STATUS

        self._method_result = value
        self.result_registry = value

    @property
    def result_registry(self):
        '''
        Return the registry of all method results
        '''
        return self._result_registry

    @result_registry.setter
    def result_registry(self, value):
        '''
        Add new result to the current method
        '''
        self._result_registry[self.method] = value

    @property
    def status(self):
        '''Current status of the plugin'''
        return self._status

    @status.setter
    def status(self, value):
        '''Set new status to the plugin'''
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
        '''Current message'''
        return self._message

    @message.setter
    def message(self, value):
        '''Set the current message'''
        self._message = value

    @property
    def boolean_status(self):
        '''Get the current boolean status of the plugin'''
        return constants.status.status_bool_mapping[self.status]

    @property
    def execution_time(self):
        '''Execution time of the plugin'''
        return self._execution_time

    @execution_time.setter
    def execution_time(self, value):
        '''Set the execution time of the plugin'''
        self._execution_time = value

    # TODO: Double check if this is used and if not evaluate if to remove it
    @property
    def raw_plugin_data(self):
        # TODO: create docstring in case is used
        return self._raw_plugin_data

    @property
    def method(self):
        '''Returns the method of the plugin that will be executed'''
        return self._method

    @property
    def default_method(self):
        '''Returns the default executable method of the plugin'''
        return self._default_method

    @property
    def methods(self):
        '''List all available executable methods'''
        return self._methods

    @property
    def context_data(self):
        '''Return the context data of the plugin'''
        return self._context_data

    @property
    def plugin_data(self):
        '''Return the plugin data of the plugin'''
        return self._plugin_data

    @property
    def plugin_options(self):
        '''Return the context options of the plugin'''
        return self._plugin_options

    @property
    def plugin_widget_id(self):
        '''Return the widget id linked to the plugin'''
        return self._plugin_widget_id

    @property
    def plugin_widget_name(self):
        '''Return the widget name linked to the plugin'''
        return self._plugin_widget_name

    @property
    def plugin_step_name(self):
        '''Return Current step name where plugin is been executed'''
        return self._plugin_step_name

    @property
    def plugin_stage_name(self):
        '''Return Current stage name where plugin is been executed'''
        return self._plugin_stage_name

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
        self._plugin_step_name = None
        self._plugin_stage_name = None

        self.register_methods()

        # Subscribe to events
        self._subscribe_events()

    @abstractmethod
    def register_methods(self):
        '''
        Function to registry all the executable methods of the plugin by the
        engine
        '''
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value=None,
        )

    def register_method(
        self, method_name, required_output_type, required_output_value
    ):
        '''
        Register given *method_name*, with the *required_output_type* and
        *required_output_value*. To be executed by the engine.
        '''

        self._methods[method_name] = {
            'required_output_type': required_output_type,
            'required_output_value': required_output_value,
        }

    def pre_execute_callback_hook(self, event):
        '''
        Method executed before calling the method given in the *event*
        should always return the event.
        '''
        return event

    def _execute_callback(self, event):
        '''Execute the method given in the *event*'''
        start_time = time.time()

        # Reset all statuses
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

        self._plugin_step_name = event['data'].get('plugin_step_name')
        self._plugin_stage_name = event['data'].get('plugin_stage_name')

        # Check method is registred
        if self.method not in self.methods.keys():
            self._status = constants.status.EXCEPTION_STATUS
            self.message = (
                "Method {} is not registred.\n Registred methods: {}".format(
                    self.method, self.methods.keys()
                )
            )
            # If booth handled by the plugin, logger the message
            self.logger.error(self.message)
            self._notify_client()
            return self.provide_plugin_info()

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
                    "status {}".format(e, self.status)
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
                self.method,
                self.context_data,
                self.plugin_data,
                self.plugin_options,
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
                options=self.plugin_options,
            )
        except Exception as e:
            self.logger.exception(e)
            if self.boolean_status:
                self._status = constants.status.EXCEPTION_STATUS
            # If status is already handled by the plugin we check if message is
            # also handled if not set a generic one
            if not self.message:
                self.message = (
                    "Error executing plugin: {} \n status {}".format(
                        e, self.status
                    )
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
        self.message = (
            "Plugin executed succesfully, result: {} \n "
            "execution messages: {}".format(self.method_result, self.message)
        )
        self._notify_client()
        # Post execute callback hook
        # reset message
        self.message = None
        try:
            # We are not setting the post_execute_result as the result for now
            # because is a free method that might not validate.
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
                    "status {}".format(e, self.status)
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

        self.message = "Post execute plugin successfully, result: {}".format(
            post_execute_result
        )
        self.status = constants.status.SUCCESS_STATUS
        end_time = time.time()
        total_time = end_time - start_time
        self.execution_time = total_time

        self._notify_client()
        return self.provide_plugin_info()

    def post_execute_callback_hook(self, result):
        '''
        Method executed after the execute method, the given *result* is the
        result of the executed method
        '''
        return result

    def provide_plugin_info(self):
        '''Provide the entire plugin information'''
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
            'plugin_context_data': self.context_data,
            'plugin_data': self.plugin_data,
            'plugin_options': self.plugin_options,
            'plugin_widget_id': self.plugin_widget_id,
            'plugin_widget_name': self.plugin_widget_name,
        }

    def _subscribe_events(self):
        '''Method to subscribe to plugin events'''
        self.event_manager.subscribe.execute_plugin(
            self.host_type, self.name, callback=self._execute_callback
        )

    def _validate_result(self, result):
        '''
        Validates the *result* of the executed method.
        '''
        is_valid = validation.validate_output_type(
            type(result), self.methods[self.method].get('required_output_type')
        )
        if not is_valid:
            self.message = (
                'Plugin result type, does not match required output type \n '
                'Result type: {} \n '
                'Required type: {}'.format(
                    type(result),
                    self.methods[self.method].get('required_output_type'),
                )
            )
            return is_valid

        if self.methods[self.method].get('required_output_value'):
            is_valid = validation.validate_output_value(
                result, self.methods[self.method].get('required_output_value')
            )
            if not is_valid:
                self.message = (
                    'Plugin result, does not match required output value \n '
                    'Result: {} \n '
                    'Required output: {}'.format(
                        result,
                        self.methods[self.method].get('required_output_value'),
                    )
                )
        return is_valid

    def run(self, context_data=None, data=None, options=None):
        '''
        Example default method with , *context_data* , *data* and *options*.

        *context_data* provides a mapping with the asset_name, context_id, asset_type_name,
        comment and status_id of the asset that we are working on.

        *data* Data to be used in the plugin

        *options* Options to pass to the plugin

        '''
        raise NotImplementedError('Missing run method.')

    def _notify_client(self):
        '''Publish an event with the plugin info to be picked by the client'''
        self.event_manager.publish.notify_plugin_progress_client(
            self.provide_plugin_info()
        )

    @classmethod
    def register(cls):
        '''
        Register function for the plugin to be discovered.
        '''
        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )
        logger.debug('registering: {} for {}'.format(cls.name, cls.host_type))

        data = {'extension_type': 'plugin', 'name': cls.name, 'cls': cls}
        return data
