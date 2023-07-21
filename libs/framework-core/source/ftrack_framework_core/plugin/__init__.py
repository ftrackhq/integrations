# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import functools
import logging
import ftrack_api
import time
import traceback
import copy
import uuid
from ftrack_framework_core import constants
from ftrack_framework_core import exception
from ftrack_framework_core import event
from ftrack_framework_core.asset import FtrackObjectManager
from ftrack_framework_core.asset.dcc_object import DccObject
from ftrack_framework_core.plugin.validation import BasePluginValidation

# TODO: Shouldn't basePlugin, somehow be an object like the definitionObject Plugin class? maybe inherit from there?
#  Maybe not. We have to double check how we want this.
# TODO: We will not have the plugins separated, all them will inherit from the
#  basePlugin and will pass the type, we will only check if the type is valid.
#  Overrides will be exposed in the core_plugins library.
# TODO: also the plugins will have the attribute widget, that the user can override but we will not have the widget type of plugin.
class BasePlugin(object):
    '''Base Class to represent a Plugin'''

    plugin_type = None
    '''Type of the plugin'''
    plugin_name = None
    '''Name of the plugin'''
    type = 'base'
    '''Type of the plugin default base. (action, collector...)'''
    category = 'plugin'
    '''Category of the plugin (plugin, plugin.widget...)'''
    host_type = constants.HOST_TYPE
    '''Host type of the plugin'''

    return_type = None
    '''Required return type'''
    return_value = None
    '''Required return Value'''
    _required_output = {}
    '''Required return exporters'''

    plugin_id = None
    '''Id of the plugin'''

    FtrackObjectManager = FtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = DccObject
    '''DccObject class to use'''

    def __repr__(self):
        return '<{}:{}>'.format(self.plugin_type, self.plugin_name)

    @property
    def ftrack_object_manager(self):
        '''
        Initializes and returns an instance of
        :class:`~ftrack_framework_core.asset.FtrackObjectManager`
        '''
        if not isinstance(
            self._ftrack_object_manager, self.FtrackObjectManager
        ):
            self._ftrack_object_manager = self.FtrackObjectManager(
                self.event_manager
            )
        return self._ftrack_object_manager

    @property
    def dcc_object(self):
        '''
        Returns the :obj:`dcc_object` from the
        :class:`~ftrack_framework_core.asset.FtrackObjectManager`
        '''
        return self.ftrack_object_manager.dcc_object

    @dcc_object.setter
    def dcc_object(self, value):
        '''
        Sets the :obj:`dcc_object` to the
        :class:`~ftrack_framework_core.asset.FtrackObjectManager`
        '''
        self.ftrack_object_manager.dcc_object = value

    @property
    def asset_info(self):
        '''
        Returns the :obj:`asset_info` from the
        :class:`~ftrack_framework_core.asset.FtrackObjectManager`
        '''
        return self.ftrack_object_manager.asset_info

    @asset_info.setter
    def asset_info(self, value):
        '''
        Sets the :obj:`asset_info` to the
        :class:`~ftrack_framework_core.asset.FtrackObjectManager`
        '''
        self.ftrack_object_manager.asset_info = value

    @property
    def output(self):
        '''Returns a copy of :attr:`required_output`'''
        return copy.deepcopy(self._required_output)

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
    def raw_plugin_data(self):
        # TODO: fix this docstring
        '''Returns the current context id'''
        return self._raw_plugin_data

    # TODO: are plugin setting the same as plugin options? If so, align it.
    #  I think are the context_data, data and options arguments that are passed to execute a plugin. But this should probbably come from the plugin_object, and also maybe we should try to clean up the event to not be that complicated.
    # TODO: update all places where using plugin_settings to self._context_data, self._plugin_data, self._options properties. re-review this.
    @property
    def plugin_settings(self):
        '''Returns the current plugin_settings'''
        return self._plugin_settings

    @property
    def method(self):
        # TODO: method is the method of the plugin that will be executed
        '''Returns the current method'''
        return self._method

    def __init__(self, session):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self.plugin_id = uuid.uuid4().hex

        self._ftrack_object_manager = None
        self._raw_plugin_data = []
        # TODO: _method: This should be a string not a list
        self._method = []
        # TODO: we should initialize self._plugin_settings in here
        self._event_manager = event.EventManager(
            session=session, mode=constants.LOCAL_EVENT_MODE
        )
        # TODO: validator should probably be a property of the plugin
        self.validator = BasePluginValidation(
            self.plugin_name,
            self._required_output,
            self.return_type,
            self.return_value,
        )

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
            'registering: {} for {}'.format(self.plugin_name, self.plugin_type)
        )

        # TODO: move the subscriptions to a standar subscription method?
        self.event_manager.subscribe.execute_plugin(
            self.host_type,
            self.category,
            self.plugin_type,
            self.plugin_name,
            callback=self._run
        )

        # subscribe to discover the plugin
        self.event_manager.subscribe.discover_plugin(
            self.host_type,
            self.category,
            self.plugin_type,
            self.plugin_name,
            callback=self._discover
        )

    # TODO: rename this to discover callback in case. But is it necesary?
    def _discover(self, event):
        '''
        Callback of
        :const:`~ftrack_framework_core.constants.DISCOVER_PLUGIN_TOPIC`
        Makes sure the plugin is discoverable for the host.

        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        return True

    # TODO: validate_run_result, as it only works for the run method
    def _validate_result(self, result):
        '''
        Validates the *result* of the :meth:`run` of the plugin using the
        :obj:`validator` and the :meth:`validator.validate_result_type`,
        :meth:`validator.validate_required_output`,
        :meth:`validator.validate_result_value`

        Returns a status and string message
        '''
        # validate result instance type
        status = constants.UNKNOWN_STATUS
        message = None
        (
            result_type_valid,
            result_type_valid_message,
        ) = self.validator.validate_result_type(result)
        if not result_type_valid:
            status = constants.ERROR_STATUS
            message = str(result_type_valid_message)
            return status, message

        # validate result with exporters options
        (
            output_valid,
            output_valid_message,
        ) = self.validator.validate_required_output(result)
        if not output_valid:
            status = constants.ERROR_STATUS
            message = str(output_valid_message)
            return status, message

        # Return value is valid
        (
            result_value_valid,
            result_value_valid_message,
        ) = self.validator.validate_result_value(result)
        if not result_value_valid:
            status = constants.ERROR_STATUS
            message = str(result_value_valid_message)
            return status, message

        status = constants.SUCCESS_STATUS
        message = 'Successfully run :{}'.format(self.__class__.__name__)
        return status, message

    def _validate_user_data(self, user_data):
        '''
        Validates the *user_data* which should contain message and data
        keys passed by the user.
        :obj:`validator` and the :meth:`validator.validate_user_data`.

        Returns a status and string message
        '''

        # validate result instance type
        (
            user_data_valid,
            user_data_validation_message,
        ) = self.validator.validate_user_data(user_data)
        if not user_data_valid:
            status = constants.ERROR_STATUS
            message = str(user_data_validation_message)
            return status, message

        status = constants.SUCCESS_STATUS
        message = 'Successfully validated user data: {}'.format(
            self.__class__.__name__
        )
        return status, message

    def _parse_run_event(self, event):
        '''
        Parse the event given on the :meth:`_run`. Returns method name to be
        executed and plugin_setting to be passed to the method.
        Also this functions saves the original passed data to the property
        :obj:`raw_plugin_data`.

        Note:: Publisher validator, exporters and Loader/Opener importer and post_importer
        plugin types override this function to modify the data that arrives to
        the plugin.
        '''
        method = event['data']['method']
        self.logger.debug('method : {}'.format(method))
        plugin_data = event['data']['plugin_data']
        plugin_options = event['data']['options']
        context_data = event['data']['context_data']
        self.logger.debug('plugin_settings : {}'.format(plugin_data, plugin_options, context_data))
        # Save a copy of the original data as _raw_plugin_data to be able to be access
        # to the original data in case we modify it for a specific plugin. So
        # the user can allways aces to self.raw_plugin_data property.
        self._raw_plugin_data = plugin_data
        return method, plugin_data, plugin_options, context_data

    def _run(self, event):
        '''
        Callback function of the event
        :const:`~ftrack_framework_core.constants.HOST_RUN_PLUGIN_TOPIC`
        Runs the method passed in the given
        *event* ['data']['pipeline']['method'].

        Returns a dictionary with the result information of the called method.

        *event* : Dictionary returned when the event topic
        :const:`~ftrack_framework_core.constants.HOST_RUN_PLUGIN_TOPIC` is
        called.

        '''
        # Having this in a separate method, we can override the parse depending
        #  on the plugin type.
        self._method, self._context_data, self._plugin_data, self._options = self._parse_run_event(event)

        start_time = time.time()

        user_data = {}

        # TODO: should this come from the definition_object? or from constants? Somewhere, we should define how a plugin is. and what should it return.
        #  Maybe having the plugin_object that inherits form the plugin definition object
        result_data = {
            'plugin_name': self.plugin_name,
            'plugin_type': self.plugin_type,
            'method': self.method,
            'status': constants.UNKNOWN_STATUS,
            'result': None,
            'execution_time': 0,
            'message': None,
            'user_data': user_data,
            'plugin_id': self.plugin_id,
        }

        # TODO: add a comment here explaining that we detect which method to run before execute the plugin
        run_fn = getattr(self, self.method)
        if not run_fn:
            message = (
                'The method : {} does not exist for the '
                'plugin:{}'.format(self.method, self.plugin_name)
            )
            self.logger.debug(message)
            result_data['status'] = constants.EXCEPTION_STATUS
            result_data['execution_time'] = 0
            result_data['message'] = str(message)
            return result_data
        try:
            result = run_fn(context_data=self.context_data, data=self.plugin_data, options=self.options)
            if isinstance(result, tuple):
                user_data = result[1]
                result = result[0]

        except Exception as message:
            end_time = time.time()
            total_time = end_time - start_time
            tb = traceback.format_exc()
            self.logger.error(message, exc_info=True)
            result_data['status'] = constants.EXCEPTION_STATUS
            result_data['execution_time'] = total_time
            result_data['message'] = str(tb)
            return result_data

        end_time = time.time()
        total_time = end_time - start_time
        result_data['execution_time'] = total_time
        # We check that the optional user_data it's a dictionary and contains
        # message and data keys.
        # TODO: can we clean up this? maybe separating it into a smaller method will be easier.
        if user_data:
            (
                user_data_status,
                user_data_validation_message,
            ) = self._validate_user_data(user_data)
            user_bool_status = constants.status_bool_mapping[user_data_status]
            if not user_bool_status:
                result_data['status'] = constants.EXCEPTION_STATUS
                result_data['message'] = str(user_data_validation_message)
                return result_data
            elif result is False:
                user_data_message = user_data.get('message')
                result_data['status'] = constants.ERROR_STATUS
                result_data['message'] = 'Failed to run {}: {}'.format(
                    self.__class__.__name__,
                    user_data_message
                    if len(user_data_message or '') > 0
                    else 'No message provided',
                )
                return result_data
        if self.method == 'run':
            status, message = self._validate_result(result)
        else:
            status = constants.SUCCESS_STATUS
            message = 'Successfully run :{}'.format(self.__class__.__name__)
        result_data['status'] = status
        result_data['message'] = message
        result_data['user_data'] = user_data

        bool_status = constants.status_bool_mapping[status]
        if bool_status:
            # TODO: somehow we should use the plugin object in here.
            result_data['result'] = {self.method: result}

        return result_data

    # tODO: this should be an ABC MEthod
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

    # TODO: this should be an EBC method
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

# TODO: cleanup this kind of imprts
from ftrack_framework_core.plugin.load import *
from ftrack_framework_core.plugin.open import *
from ftrack_framework_core.plugin.publish import *
from ftrack_framework_core.plugin.asset_manager import *
from ftrack_framework_core.plugin.resolver import *
