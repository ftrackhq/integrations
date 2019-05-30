# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import ftrack_api
import time
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import exception
from ftrack_connect_pipeline.client.widgets import BaseWidget


class _Base(object):

    plugin_type = None
    plugin_name = None
    type = None
    host = constants.HOST
    ui = constants.UI
    return_type = None
    input_options = []
    output_options = []

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

    def _base_topic(self, topic):
        return NotImplementedError()

    def __init__(self, session):
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._session = session

    def register(self):
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        self.logger.debug('registering: {} for {}'.format(
            self.plugin_name, self.plugin_type)
        )

        self.session.event_hub.subscribe(
            self.run_topic, self._run
        )

        self.session.event_hub.subscribe(
            self.discover_topic, self._discover
        )

    def _discover(self, event):
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        return True

    def run(self, context=None, data=None, options=None):
        raise NotImplementedError('Missing run method.')

    def _validate_input_options(self, settings):
        if settings.get('options'):
            for input_option in self.input_options:
                if input_option not in settings['options']:
                    message = '{} require {} input option'.format(
                            self.__class__.__name__, input_option
                        )
                    return False, message
        return True, ""

    def _validate_result_options(self, result):
        for output_option in self.output_options:
            if output_option not in result:
                message = '{} require {} result option'.format(
                    self.__class__.__name__, output_option
                )
                return False, message
        return True, ""

    def _validate_result_type(self, result):
        if self.return_type:
            if not isinstance(result, self.return_type):
                message = 'Return value of {} is of type {}, should {} type'.format(
                    self.__class__.__name__, type(result), self.return_type
                )
                return False, message

        return True, ""

    def _run(self, event):
        return_value = {'status': constants.UNKNOWN_STATUS, 'result': 'Something went wrong...', 'execution_time': 0}
        result = None

        settings = event['data']['settings']
        input_valid, message = self._validate_input_options(settings)
        if not input_valid:
            return_value = {'status': constants.ERROR_STATUS, 'result': str(message), 'execution_time': 0}

        start_time = time.time()

        try:
            result = self.run(**settings)
        except Exception as message:
            end_time = time.time()
            total_time = end_time - start_time
            return_value = {'status': constants.EXCEPTION_STATUS, 'result': str(message), 'execution_time': total_time}

        end_time = time.time()
        total_time = end_time - start_time

        output_valid, message = self._validate_result_options(result)
        if not output_valid:
            return_value = {'status': constants.ERROR_STATUS, 'result': str(message), 'execution_time': total_time}

        result_valid, message = self._validate_result_type(result)
        if not result_valid:
            return_value = {'status': constants.ERROR_STATUS, 'result': str(message), 'execution_time': total_time}
        else:
            return_value = {'status': constants.SUCCESS_STATUS, 'result': result, 'execution_time': total_time}

        self.logger.info('run result for {} with result {}'.format(self.__class__.__name__, return_value))
        return return_value


class BasePlugin(_Base):
    type = 'plugin'

    def _base_topic(self, topic):
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


class BaseWidget(_Base):
    type = 'widget'
    return_type = BaseWidget

    def _base_topic(self, topic):
        required = [
            self.host,
            self.type,
            self.plugin_type,
            self.plugin_name,
            self.ui
        ]

        if not all(required):
            raise exception.PluginError('Some required fields are missing')

        topic = constants.WIDGET_EVENT.format(
            topic,
            self.host,
            self.ui,
            self.type,
            self.plugin_type,
            self.plugin_name
        )
        return topic


class ContextPlugin(BasePlugin):
    return_type = dict
    plugin_type = constants.CONTEXT
    input_options = ['context_id']
    output_options = ['context_id', 'asset_name', 'comment', 'status_id']


class ContextWidget(BaseWidget):
    plugin_type = constants.CONTEXT


from ftrack_connect_pipeline.plugin.load import *
from ftrack_connect_pipeline.plugin.publish import *