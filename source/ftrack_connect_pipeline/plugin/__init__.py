# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
import time
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline.plugin.validation import PluginValidation

class BasePlugin(object):

    plugin_type = None
    plugin_name = None
    type = 'plugin'#None
    host = constants.HOST

    #ui = constants.UI #No needed for now

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

        topic = constants.PLUGIN_EVENT.format(
            topic,
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name
        )
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
        print "we are discovering the plugin, event ---> {}".format(event)
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        return True

    def _run(self, event):
        '''Function that executes the plugin used by the runner, called by the PIPELINE_RUN_PLUGIN_TOPIC.
        returns a dictionary with the status, result and message of the execution'''

        #TODO: what event['target'] is expected to be used for?
        # and the same whith event['in_reply_to_event'] and event['sent']

        #print "we are _running the plugin, event ---> {}".format(event)


        plugin_settings = event['data']['settings']

        plugin_validator = PluginValidation(self.plugin_name, self.input_options, self.output_options, self.return_type,
                                            self.return_value)

        # validate input options
        input_valid, message = plugin_validator.validate_input_options(plugin_settings)
        if not input_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': 0, 'message': str(message)}

        # run Plugin
        start_time = time.time()
        try:
            result = self.run(**plugin_settings)
            #print "this is the reurning data of the plugin {} ---> {}".format(self.plugin_name, result)
        except Exception as message:
            end_time = time.time()
            total_time = end_time - start_time
            self.logger.debug(message, exc_info=True)
            return {'status': constants.EXCEPTION_STATUS, 'result': None, 'execution_time': total_time, 'message': str(message)}
        end_time = time.time()
        total_time = end_time - start_time

        # TODO we should change the validation order: validate result_type, validate result_value, validate result_options

        # validate result with output options
        output_valid, output_valid_message = plugin_validator.validate_result_options(result)
        if not output_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time, 'message': str(output_valid_message)}

        # validate result instance type
        result_type_valid, result_type_valid_message = plugin_validator.validate_result_type(result)
        if not result_type_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time, 'message': str(result_type_valid_message)}

        # Return value is valid
        result_value_valid, result_value_valid_message = plugin_validator.validate_result_value(result)
        if not result_value_valid:
            return {'status': constants.ERROR_STATUS, 'result': None, 'execution_time': total_time, 'message': str(result_value_valid_message)}

        return {'status': constants.SUCCESS_STATUS, 'result': result, 'execution_time': total_time, 'message': 'Successfully run :{}'.format(self.__class__.__name__)}

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
