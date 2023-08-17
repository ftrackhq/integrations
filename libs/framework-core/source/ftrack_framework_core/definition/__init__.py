# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
from functools import partial

import ftrack_api

import ftrack_constants.framework as constants

from ftrack_framework_core import event

logger = logging.getLogger(__name__)

# TODO: if we decide to not communicate definitions with events this can be
#  removed. If we decide the contrary, evanluate to put this in a separated
#  library called ftrack_framework_definition.
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
            session=session, mode=constants.event.LOCAL_EVENT_MODE
        )

    def register(self, path):
        '''
        Register the definition subscribing to the
        DISCOVER_DEFINITION_TOPIC event
        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        self.event_manager.subscribe.discover_definition(self._register_definitions_callback, path)

    # TODO: rename to register_definitions_callback.
    def _register_definitions_callback(self, event, path):
        '''
        Callback method that returns the registred host_types and
        definition_paths of the discovered definitions
        '''
        host_types = event['data']['host_types']
        definition_paths = os.getenv("FTRACK_DEFINITION_PATH").split(
            os.pathsep
        )
        # TODO: we add the path to an environment variable for now and return that variable?
        data = {"host_types": host_types, "definition_paths": definition_paths}
        return data


class Definition(BaseDefinition):
    '''Base Class to represent a Definition'''

    def __init__(self, session):
        '''
        Initialise BaseDefinition with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(Definition, self).__init__(session)
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

    def register(self, path):
        '''
        Register the definition subscribing to the
        DISCOVER_DEFINITION_TOPIC event
        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return
        self.event_manager.subscribe.discover_definition(partial(self._register_definitions_callback, path))

    # TODO: rename to register_definitions_callback.
    def _register_definitions_callback(self, path, event):
        '''
        Callback method that returns the registred host_types and
        definition_paths of the discovered definitions
        '''
        print("subscription callback path: {}, event: {}".format(path, event))
        host_types = event['data']['host_types']
        data = {"host_types": host_types, "definition_path": path}
        return data


class Schema(BaseDefinition):
    '''Base Class to represent a Definition'''

    def __init__(self, session):
        '''
        Initialise BaseDefinition with instance of
        :class:`ftrack_api.session.Session`
        '''
        super(Schema, self).__init__(session)
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

    def register(self):
        '''
        Register the definition subscribing to the
        DISCOVER_DEFINITION_TOPIC event
        '''
        if not isinstance(self.session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        self.event_manager.subscribe.discover_definition(self._register_shcema_callback)

    # TODO: rename to register_definitions_callback.
    def _register_shcema_callback(self, event):
        '''
        Callback method that returns the registred host_types and
        definition_paths of the discovered definitions
        '''
        host_types = event['data']['host_types']
        definition_paths = os.getenv("FTRACK_SCHEMA_PATH").split(
            os.pathsep
        )
        data = {"host_types": host_types, "schema_paths": definition_paths}
        return data
