# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import uuid
import logging
import ftrack_api
from ftrack_framework_core import event
from ftrack_framework_core import constants

logger = logging.getLogger(__name__)


class BaseDefinition(object):
    '''Base Class to represent a Definition'''

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

    def __init__(self, session):
        '''
        Initialise BaseDefinition with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._raw_data = []
        self._method = []
        self._event_manager = event.EventManager(
            session=session, mode=constants.LOCAL_EVENT_MODE
        )

    def register(self):
        '''
        Register the definition subscribing to the
        DISCOVER_DEFINITION_TOPIC event
        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        self.event_manager.subscribe.discover_definition(self._register_definitions_callback)

    # TODO: rename to register_definitions_callback.
    def _register_definitions_callback(self, event):
        '''
        Callback method that returns the registred host_types and
        definition_paths of the discovered definitions
        '''
        host_types = event['data']['host_types']
        definition_paths = os.getenv("FTRACK_DEFINITION_PATH").split(
            os.pathsep
        )
        data = {"host_types": host_types, "definition_paths": definition_paths}
        return data
