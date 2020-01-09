# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
import time
import copy
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import exception


class BasePluginValidation(object):
    '''Plugin Validation base class'''

    def __init__(self, plugin_name, required_output, return_type, return_value):
        '''Initialise PluginValidation with *plugin_name*, *required_output*,
        *return_type*, *return_value*.

        *plugin_name* current plugin name stored at the plugin base class

        *required_output* required output of the current plugin stored at
        _required_output of the plugin base class

        *return_type* return type of the current plugin stored at the plugin
        base class

        *return_value* return value of the current plugin stored at the
        plugin base class
        '''
        super(BasePluginValidation, self).__init__()
        self.plugin_name = plugin_name
        self.required_output = required_output
        self.return_type = return_type
        self.return_value = return_value

    # def validate_required_input_options(self, settings):
    #     '''This function checks that the plugin settings contains all
    #     the expected input_options defined for the specific plugin type'''
    #
    #     validator_result = (True, "")
    #     for input_option in self.required_input_options:
    #         if settings.get('options'):
    #             if input_option not in settings['options']:
    #                 message = '{} require {} input option'.format(
    #                     self.plugin_name, input_option
    #                 )
    #                 validator_result = (False, message)
    #         else:
    #             message = '{} require {} input options'.format(
    #                 self.plugin_name, self.required_input_options
    #             )
    #             validator_result = (False, message)
    #     return validator_result

    def validate_required_output(self, result):
        '''Ensures that *result* contains all the expected required_output keys
                defined for the current plugin.

                *result* output value of the plugin execution

                Return tuple (bool,str)
                '''
        validator_result = (True, "")

        for output_key in self.required_output.keys():
            if output_key not in result.keys():
                message = '{} require {} result option'.format(
                    self.plugin_name, output_key
                )
                validator_result = (False, message)

        return validator_result

    def validate_result_type(self, result):
        '''Ensures that *result* is instance of the defined return_type of
        the current plugin.

        *result* output value of the plugin execution

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        if self.return_type is not None:
            if not isinstance(result, self.return_type):
                message = 'Return value of {} is of type {}, should {} ' \
                          'type'.format(self.plugin_name, type(result),
                                        self.return_type)
                validator_result = (False, message)

        return validator_result

    def validate_result_value(self, result):
        '''Ensures that *result* is equal as the defined return_value of
        the current plugin.

        *result* output value of the plugin execution

        Return tuple (bool,str)
        '''
        validator_result = (True, "")

        # if self.return_value is not None:
        #
        #     if result != self.return_value:
        #         message = 'Return value of {} is not {}'.format(
        #             self.__class__.__name__, self.return_value
        #         )
        #         validator_result = (False, message)

        return validator_result


class BasePlugin(object):
    ''' Class representing a Plugin '''
    plugin_type = None
    plugin_name = None
    type = 'plugin'#None
    host = constants.HOST

    return_type = None
    return_value = None
    _required_output = {}

    def __repr__(self):
        return '<{}:{}>'.format(self.plugin_type, self.plugin_name)

    @property
    def output(self):
        ''' Returns a copy of required_output '''
        return copy.deepcopy(self._required_output)

    @property
    def discover_topic(self):
        '''Return a formated PIPELINE_DISCOVER_PLUGIN_TOPIC'''
        return self._base_topic(constants.PIPELINE_DISCOVER_PLUGIN_TOPIC)

    @property
    def run_topic(self):
        '''Return a formated PIPELINE_RUN_PLUGIN_TOPIC'''
        return self._base_topic(constants.PIPELINE_RUN_PLUGIN_TOPIC)

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session):
        '''Initialise BasePlugin with *session*.

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._session = session
        self.validator = BasePluginValidation(self.plugin_name,
                                          self._required_output,
                                          self.return_type, self.return_value)

    def _base_topic(self, topic):
        '''Ensures that we pass all the needed information to the topic
        with *topic*.

        *topic* topic base value

        Return formated topic

        Raise :exc:`ftrack_connect_pipeline.exception.PluginError` if some
        information is missed.
        '''


        required = [
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name,
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = 'topic={} and data.pipeline.host={} and data.pipeline.type={} ' \
                'and data.pipeline.plugin_type={} and ' \
                'data.pipeline.plugin_name={}'.format(topic, self.host,
                                                      self.type,
                                                      self.plugin_type,
                                                      self.plugin_name)

        return topic

    def register(self):
        '''Called by each plugin to register them self.

        .. note::

            This function subscribes the plugin to two event topics:
            PIPELINE_DISCOVER_PLUGIN_TOPIC: Topic to make the plugin discoverable
            for the host.
            PIPELINE_RUN_PLUGIN_TOPIC: Topic to execute the plugin
        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        self.logger.debug('registering: {} for {}'.format(
            self.plugin_name, self.plugin_type)
        )

        self.session.event_hub.subscribe(
            self.run_topic,
            self._run
        )

        # subscribe to discover the plugin
        self.session.event_hub.subscribe(
            self.discover_topic,
            self._discover
        )

    def _discover(self, event):
        '''Makes sure the plugin is discoverable for the host.

        *event* not used.

        .. note::

            Called by PIPELINE_DISCOVER_PLUGIN_TOPIC
        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        return True

    def _run(self, event):
        '''Run the current plugin with the settings form the *event*.

        *event* provides a dictionary with the plugin schema information.

        Returns a dictionary with the status, result, execution time and
        message of the execution

        .. note::

            This function is used by the host engine and called by the
            PIPELINE_RUN_PLUGIN_TOPIC

        '''

        plugin_settings = event['data']['settings']


        # # validate input options
        # input_valid, message = self.validator.validate_required_input_options(plugin_settings)
        # if not input_valid:
        #     return {'status': constants.ERROR_STATUS, 'result': None,
        #             'execution_time': 0, 'message': str(message)}

        # run Plugin
        start_time = time.time()
        try:
            result = self.run(**plugin_settings)

        except Exception as message:
            end_time = time.time()
            total_time = end_time - start_time
            self.logger.debug(message, exc_info=True)
            return {'status': constants.EXCEPTION_STATUS, 'result': None,
                    'execution_time': total_time,
                    'message': str(message)}
        end_time = time.time()
        total_time = end_time - start_time

        # validate result instance type
        result_type_valid, result_type_valid_message = self.validator.validate_result_type(
            result)
        if not result_type_valid:
            return {'status': constants.ERROR_STATUS, 'result': None,
                    'execution_time': total_time,
                    'message': str(result_type_valid_message)}

        # validate result with output options
        output_valid, output_valid_message = self.validator.validate_required_output(
            result)
        if not output_valid:
            return {'status': constants.ERROR_STATUS, 'result': None,
                    'execution_time': total_time,
                    'message': str(output_valid_message)}

        # Return value is valid
        result_value_valid, result_value_valid_message = self.validator.validate_result_value(
            result)
        if not result_value_valid:
            return {'status': constants.ERROR_STATUS, 'result': None,
                    'execution_time': total_time,
                    'message': str(result_value_valid_message)}

        return {'status': constants.SUCCESS_STATUS, 'result': result,
                'execution_time': total_time,
                'message': 'Successfully run :{}'.format(self.__class__.__name__)}

    def run(self, context=None, data=None, options=None):
        '''Run the current plugin with , *context* , *data* and *options*.

        *context* provides a mapping with the asset_name, context_id, asset_type,
        comment and status_id of the asset that we are working on.

        *data* a list of data coming from previous collector or empty list

        *options* a dictionary of options passed from outside.

        Returns self.output dictionary, list or boolean.

        Raise NotImplementedError

        .. note::

            Use always self.output as a base to return the values,
            don't override self.output as it contains the _required_output

        '''
        raise NotImplementedError('Missing run method.')


from ftrack_connect_pipeline.plugin.load import *
from ftrack_connect_pipeline.plugin.collector import *
from ftrack_connect_pipeline.plugin.context import *
from ftrack_connect_pipeline.plugin.finaliser import *
from ftrack_connect_pipeline.plugin.output import *
from ftrack_connect_pipeline.plugin.validator import *