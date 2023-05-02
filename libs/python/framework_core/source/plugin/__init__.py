# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import functools
import logging
import ftrack_api
import time
import traceback
import copy
import uuid
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline import event
from ftrack_connect_pipeline.asset import FtrackObjectManager
from ftrack_connect_pipeline.asset.dcc_object import DccObject


class BasePluginValidation(object):
    '''Plugin Validation base class'''

    def __init__(
        self, plugin_name, required_output, return_type, return_value
    ):
        '''
        Initialise PluginValidation with *plugin_name*, *required_output*,
        *return_type*, *return_value*.

        *plugin_name* : current plugin name.

        *required_output* : required exporters of the current plugin.

        *return_type* : required return type of the current plugin.

        *return_value* : Expected return value of the current plugin.
        '''
        super(BasePluginValidation, self).__init__()
        self.plugin_name = plugin_name
        self.required_output = required_output
        self.return_type = return_type
        self.return_value = return_value

    def validate_required_output(self, result):
        '''
        Ensures that *result* contains all the expected :obj:`required_output`
        keys defined for the current plugin.

        *result* : exporters value of the plugin execution.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        for output_key in list(self.required_output.keys()):
            if output_key not in list(result.keys()):
                message = '{} require {} result option'.format(
                    self.plugin_name, output_key
                )
                validator_result = (False, message)

        return validator_result

    def validate_result_type(self, result):
        '''
        Ensures that *result* is instance of the defined :obj:`return_type` of
        the current plugin.

        *result* : exporters value of the plugin execution.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        if self.return_type is not None:
            if not isinstance(result, self.return_type):
                message = (
                    'Return value of {} is of type {}, should be {} '
                    'type'.format(
                        self.plugin_name, type(result), self.return_type
                    )
                )

                validator_result = (False, message)

        return validator_result

    def validate_result_value(self, result):
        '''Ensures that *result* is equal as the defined :obj:`return_value` of
        the current plugin.

        *result* : exporters value of the plugin execution.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        return validator_result

    def validate_user_data(self, user_data):
        '''
        Ensures that *user_data* is instance of :obj:`dict`. And validates that
        contains message and data keys.

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        if user_data is not None:
            if not isinstance(user_data, dict):
                message = (
                    'user_data value should be of type {} and it\'s '
                    'type of {}'.format(type(dict), type(user_data))
                )
                validator_result = (False, message)
            else:
                if not 'message' in list(user_data.keys()):
                    user_data['message'] = ''
                if not 'data' in list(user_data.keys()):
                    user_data['data'] = {}
                for key in list(user_data.keys()):
                    if not key in ['message', 'data']:
                        validator_result = (
                            False,
                            'user_data can only contain they keys "message" '
                            'and/or "data"',
                        )
                        break
        return validator_result


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
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
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
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        return self.ftrack_object_manager.dcc_object

    @dcc_object.setter
    def dcc_object(self, value):
        '''
        Sets the :obj:`dcc_object` to the
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        self.ftrack_object_manager.dcc_object = value

    @property
    def asset_info(self):
        '''
        Returns the :obj:`asset_info` from the
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        return self.ftrack_object_manager.asset_info

    @asset_info.setter
    def asset_info(self, value):
        '''
        Sets the :obj:`asset_info` to the
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        self.ftrack_object_manager.asset_info = value

    @property
    def output(self):
        '''Returns a copy of :attr:`required_output`'''
        return copy.deepcopy(self._required_output)

    @property
    def discover_topic(self):
        '''Return a formatted PIPELINE_DISCOVER_PLUGIN_TOPIC'''
        return self._base_topic(constants.PIPELINE_DISCOVER_PLUGIN_TOPIC)

    @property
    def run_topic(self):
        '''Return a formatted PIPELINE_RUN_PLUGIN_TOPIC'''
        return self._base_topic(constants.PIPELINE_RUN_PLUGIN_TOPIC)

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
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        return self._event_manager

    @property
    def raw_data(self):
        '''Returns the current context id'''
        return self._raw_data

    @property
    def plugin_settings(self):
        '''Returns the current plugin_settings'''
        return self._plugin_settings

    @property
    def method(self):
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
        self._raw_data = []
        self._method = []
        self._event_manager = event.EventManager(
            session=session, mode=constants.LOCAL_EVENT_MODE
        )
        self.validator = BasePluginValidation(
            self.plugin_name,
            self._required_output,
            self.return_type,
            self.return_value,
        )

    def _base_topic(self, topic):
        '''
        Ensures that :attr:`host_type`, :attr:`category`, :attr:`plugin_type`,
        :attr:`plugin_name` are defined and Returns a formatted topic of an event
        for the given *topic*

        *topic* topic base value

        Raise :exc:`ftrack_connect_pipeline.exception.PluginError` if some
        information is missed.
        '''

        required = [
            self.host_type,
            self.category,
            self.plugin_type,
            self.plugin_name,
        ]
        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = (
            'topic={} and data.pipeline.host_type={} and '
            'data.pipeline.category={} and data.pipeline.plugin_type={} and '
            'data.pipeline.plugin_name={}'
        ).format(
            topic,
            self.host_type,
            self.category,
            self.plugin_type,
            self.plugin_name,
        )

        return topic

    def register(self):
        '''
        Register function of the plugin to regiter it self.

        .. note::

            This function subscribes the plugin to two
            :class:`ftrack_api.event.base.Event` topics:

            :const:`~ftrack_connect_pipeline.constants.PIPELINE_DISCOVER_PLUGIN_TOPIC`:
            Topic to make the plugin discoverable for the host.

            :const:`~ftrack_connect_pipeline.constants.PIPELINE_RUN_PLUGIN_TOPIC`:
            Topic to execute the plugin
        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        self.logger.debug(
            'registering: {} for {}'.format(self.plugin_name, self.plugin_type)
        )

        self.session.event_hub.subscribe(self.run_topic, self._run)

        # subscribe to discover the plugin
        self.session.event_hub.subscribe(self.discover_topic, self._discover)

    def _discover(self, event):
        '''
        Callback of
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_DISCOVER_PLUGIN_TOPIC`
        Makes sure the plugin is discoverable for the host.

        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        return True

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
        :obj:`raw_data`.

        Note:: Publisher validator, exporters and Loader/Opener importer and post_importer
        plugin types override this function to modify the data that arrives to
        the plugin.
        '''
        method = event['data']['pipeline']['method']
        self.logger.debug('method : {}'.format(method))
        plugin_settings = event['data']['settings']
        self.logger.debug('plugin_settings : {}'.format(plugin_settings))
        # Save a copy of the original data as _raw_data to be able to be access
        # to the original data in case we modify it for a specific plugin. So
        # the user can allways aces to self.raw_data property.
        self._raw_data = plugin_settings.get('data')
        return method, plugin_settings

    def _run(self, event):
        '''
        Callback function of the event
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_RUN_PLUGIN_TOPIC`
        Runs the method passed in the given
        *event* ['data']['pipeline']['method'].

        Returns a dictionary with the result information of the called method.

        *event* : Dictionary returned when the event topic
        :const:`~ftrack_connect_pipeline.constants.PIPELINE_RUN_PLUGIN_TOPIC` is
        called.

        '''
        # Having this in a separate method, we can override the parse depending
        #  on the plugin type.
        self._method, self._plugin_settings = self._parse_run_event(event)

        start_time = time.time()

        user_data = {}

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
            result = run_fn(**self.plugin_settings)
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
            result_data['result'] = {self.method: result}

        return result_data

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


from ftrack_connect_pipeline.plugin.load import *
from ftrack_connect_pipeline.plugin.open import *
from ftrack_connect_pipeline.plugin.publish import *
from ftrack_connect_pipeline.plugin.asset_manager import *
