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

    name = None

    def __repr__(self):
        return '<{}>'.format(self.name)

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._session

    @property
    def id(self):
        '''
        Id of the plugin
        '''
        return self._id

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

    @property
    def options(self):
        '''Return the context options of the plugin'''
        return self._options

    @property
    def ui_id(self):
        '''Return the widget id linked to the plugin'''
        return self._ui_id

    @property
    def ui_name(self):
        '''Return the widget name linked to the plugin'''
        return self._ui_name

    @property
    def result(self):
        '''Return the widget name linked to the plugin'''
        return self._result

    def __init__(self, options, session):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._options = options
        self._session = session
        self._id = uuid.uuid4().hex
        self._status = constants.status.UNKNOWN_STATUS
        self._message = ''
        self._execution_time = 0
        self._ui_id = None
        self._ui_name = None
        self._result = False

    @abstractmethod
    def run(self, store):
        raise NotImplementedError('Missing run method.')

    def run_plugin(self, store):
        start_time = time.time()
        # Reset all statuses
        self._status = constants.status.DEFAULT_STATUS
        self._message = None
        self._result = None
        try:
            self.status = constants.status.RUNNING_STATUS
            self._result = self.run(store)
        except Exception as e:
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
            self.logger.exception(
                "Error message: {}\n Traceback: {}".format(self.message, e)
            )
            return self.provide_plugin_info()
        # print plugin error handled by the plugin
        if not self.boolean_status:
            # Generic message printing the result in case no message is provided.
            if not self.message:
                self.message = (
                    "Error detected on the plugin {}, but no message provided. "
                    "Result is {}.".format(self.name, self.result)
                )
            self.logger.error(self.message)
            return self.provide_plugin_info()

        self.status = constants.status.SUCCESS_STATUS
        # Notify client
        self.message = (
            "Plugin executed successfully, result: {} \n "
            "execution messages: {}".format(self.result, self.message)
        )
        end_time = time.time()
        total_time = end_time - start_time
        self.execution_time = total_time

        return self.provide_plugin_info()

    def provide_plugin_info(self):
        '''Provide the entire plugin information'''
        return {
            'plugin_name': self.name,
            'plugin_id': self.id,
            'plugin_boolean_status': self.boolean_status,
            'plugin_status': self.status,
            'plugin_message': self.message,
            'plugin_execution_time': self.execution_time,
            'plugin_ui_id': self.ui_id,
            'plugin_ui_name': self.ui_name,
            'plugin_result': self.result,
        }

    @classmethod
    def register(cls):
        '''
        Register function for the plugin to be discovered.
        '''
        import inspect

        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )
        logger.debug('registering: {}'.format(cls.name))

        data = {
            'extension_type': 'plugin',
            'name': cls.name,
            'extension': cls,
            'path': inspect.getfile(cls),
        }
        return data
