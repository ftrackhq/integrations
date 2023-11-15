# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging
import time
import uuid
from abc import ABC, abstractmethod

import ftrack_constants.framework as constants


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
    def result(self):
        '''Return the result provided by the plugin'''
        return self._result

    @property
    def reference(self):
        '''Return the reference number given to the plugin'''
        return self._reference

    def __init__(self, options, session, reference_id=None):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._options = options
        self._session = session
        self._status = constants.status.UNKNOWN_STATUS
        self._message = ''
        self._execution_time = 0
        self._result = False
        self._reference = reference_id

    def ui_hook(self, payload):
        '''
        Method to interact with the UI.
        *payload* Data provided from the ui.
        '''
        raise NotImplementedError('Missing ui_hook method.')

    @abstractmethod
    def run(self, store):
        '''
        Implementation of the plugin. *store* contains any previous published
        data from the executed tool-config
        '''
        raise NotImplementedError('Missing run method.')

    def run_plugin(self, store):
        '''
        Call the method run of the current plugin and provides feedback to the
        engine.
        *store* contains any previous published data from the executed
        tool-config
        '''
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
            return self.provide_plugin_info(store)
        # print plugin error handled by the plugin
        if not self.boolean_status:
            # Generic message printing the result in case no message is provided.
            if not self.message:
                self.message = (
                    "Error detected on the plugin {}, but no message provided. "
                    "Result is {}.".format(self.name, self.result)
                )
            self.logger.error(self.message)
            return self.provide_plugin_info(store)

        self.status = constants.status.SUCCESS_STATUS
        # Notify client
        self.message = (
            "Plugin executed successfully, result: {} \n "
            "execution messages: {}".format(self.result, self.message)
        )
        end_time = time.time()
        total_time = end_time - start_time
        self.execution_time = total_time

        return self.provide_plugin_info(store)

    def provide_plugin_info(self, store=None):
        '''
        Provide the entire plugin information.
        If *store* is given, provides the current store as part of the
        plugin info.
        '''
        return {
            'plugin_name': self.name,
            'plugin_reference': self.reference,
            'plugin_boolean_status': self.boolean_status,
            'plugin_status': self.status,
            'plugin_message': self.message,
            'plugin_execution_time': self.execution_time,
            'plugin_options': self.options,
            'plugin_result': self.result,
            'plugin_store': store,
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
