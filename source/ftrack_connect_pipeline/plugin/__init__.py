# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
import time
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import exception


class PluginValidation(object):

    def __init__(self, plugin_name, input_options, output_options, return_type, return_value):
        super(PluginValidation, self).__init__()
        self.plugin_name = plugin_name
        self.input_options = input_options
        self.output_options = output_options
        self.return_type = return_type
        self.return_value = return_value

    def validate_input_options(self, settings):
        '''This function checks that the plugin settings contains all the expected input_options
            defined for the specific plugin type'''
        validator_result = (True, "")
        if settings.get('options'):
            for input_option in self.input_options:
                if input_option not in settings['options']:
                    message = '{} require {} input option'.format(
                        self.plugin_name, input_option
                    )
                    validator_result = (False, message)

        return validator_result


    def validate_result_options(self, result):
        '''This function checks that the plugin result contains all the expected output_options
        defined for the specific plugin type'''
        validator_result = (True, "")

        for output_option in self.output_options:

            if output_option not in result:
                message = '{} require {} result option'.format(
                    self.plugin_name, output_option
                )
                validator_result = (False, message)

        return validator_result

    def validate_result_type(self, result):
        '''This function checks that the plugin result is instance
        of the defined return_type for the specific plugin type'''
        validator_result = (True, "")

        if self.return_type is not None:
            if not isinstance(result, self.return_type):
                message = 'Return value of {} is of type {}, should {} type'.format(
                    self.plugin_name, type(result), self.return_type
                )
                validator_result = (False, message)

        return validator_result


    def validate_result_value(self, result):
        '''This function checks if plugin result is equal as the expected
        defined return_value for the specific plugin type'''
        validator_result = (True, "")

        if self.return_value is not None:

            if result != self.return_value:
                message = 'Return value of {} is not {}'.format(
                    self.__class__.__name__, self.return_value
                )
                validator_result = (False, message)

        return validator_result

class BasePlugin(object):

    plugin_type = None
    plugin_name = None
    type = 'plugin'#None
    host = constants.HOST

    return_type = None
    return_value = None
    input_options = []
    output_options = []

    def __repr__(self):
        return '<{}:{}>'.format(self.plugin_type, self.plugin_name)

    @property
    def discover_topic(self):
        return self._base_topic(constants.PIPELINE_DISCOVER_PLUGIN_TOPIC)

    @property
    def run_topic(self):
        return self._base_topic(constants.PIPELINE_RUN_PLUGIN_TOPIC)

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session):
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._session = session
        self.validator = PluginValidation(self.plugin_name, self.input_options, self.output_options,
                                          self.return_type, self.return_value)

    def _base_topic(self, topic):
        '''This function ensures that we pass all the nedded information to the topic
        Return formated topic

        Raise :exc:`ftrack_connect_pipeline.exception.PluginError` if some information is missed.
        '''

        required = [
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name,
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = 'topic={} and data.pipeline.host={} and data.pipeline.type={} and data.pipeline.plugin_type={} and ' \
                'data.pipeline.plugin_name={}'.format(topic, self.host, self.type, self.plugin_type, self.plugin_name)

        return topic

    def register(self):
        '''Function called by each plugin to register them self.
        This function subscribes the plugin to two event topics:
        PIPELINE_DISCOVER_PLUGIN_TOPIC: Topic to make the plugin discoverable for the host
        PIPELINE_RUN_PLUGIN_TOPIC: Topic to execute the plugin'''
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
        '''This function makes sure the plugin is discoverable for the host,
        called by PIPELINE_DISCOVER_PLUGIN_TOPIC'''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        return True

    def _run(self, event):
        '''Function that executes the plugin used by the runner, called by the PIPELINE_RUN_PLUGIN_TOPIC.
        returns a dictionary with the status, result and message of the execution'''

        plugin_settings = event['data']['settings']

        # validate input options
        input_valid, message = self.validator.validate_input_options(plugin_settings)
        if not input_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': 0, 'message': str(message)}

        # run Plugin
        start_time = time.time()
        try:
            result = self.run(**plugin_settings)

        except Exception as message:
            end_time = time.time()
            total_time = end_time - start_time
            self.logger.debug(message, exc_info=True)
            return {'status': constants.EXCEPTION_STATUS, 'result': None, 'execution_time': total_time,
                    'message': str(message)}
        end_time = time.time()
        total_time = end_time - start_time

        # validate result with output options
        output_valid, output_valid_message = self.validator.validate_result_options(result)
        if not output_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time,
                    'message': str(output_valid_message)}

        # validate result instance type
        result_type_valid, result_type_valid_message = self.validator.validate_result_type(result)
        if not result_type_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time,
                    'message': str(result_type_valid_message)}

        # Return value is valid
        result_value_valid, result_value_valid_message = self.validator.validate_result_value(result)
        if not result_value_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time,
                    'message': str(result_value_valid_message)}

        return {'status': constants.SUCCESS_STATUS, 'result': result, 'execution_time': total_time,
                'message': 'Successfully run :{}'.format(self.__class__.__name__)}

    def run(self, context=None, data=None, options=None):
        '''plugin execution function of each plugin, should be overrided in the plugin itself

        context argument: context of the task that we are working on
        data: coming from the previous stage, if context or collector stage, data is empty
        options: plugin options
        returns dictionary or list with data
        '''
        raise NotImplementedError('Missing run method.')


from ftrack_connect_pipeline.plugin.load import *
from ftrack_connect_pipeline.plugin.collector import *
from ftrack_connect_pipeline.plugin.context import *
from ftrack_connect_pipeline.plugin.finaliser import *
from ftrack_connect_pipeline.plugin.output import *
from ftrack_connect_pipeline.plugin.validator import *
