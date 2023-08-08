# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import uuid


class BaseWidget(object):
    '''Base Class to represent a Plugin'''

    # We Define name, plugin_type and host_type as class variables for
    # convenience for the user when creating its own plugin.
    name = None
    # TODO: framework_dialog and framework_widget for the child classes
    widget_type = 'framework_base'
    client_method_connection = None
    client_property_setter_connection = None
    client_property_getter_connection = None

    def __repr__(self):
        return '<{}:{}>'.format(self.id, self.name)

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
    def id(self):
        '''
        Id of the plugin
        '''
        return self._id

    @property
    def definition(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('definition')

    @definition.setter
    def definition(self, value):
        '''
        Dependency framework widgets
        '''
        self.client_property_setter_connection('definition', value)

    @property
    def plugins(self):
        '''
        Dependency framework widgets
        '''
        if not self.definition:
            self.logger.warning("Please set a definition before quering plugins")
            return None
        return self.definition.get_all(category='plugin')

    def __init__(self, event_manager):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._event_manager = event_manager
        self._id = uuid.uuid4().hex

        # Set properties to 0
        self._definition = None

        self.pre_build()
        self.build()
        self.post_build()

    def connect_methods(self, method):
        self.client_method_connection = method

    def connect_properties(self, set_method, get_method):
        self.client_property_setter_connection = set_method
        self.client_property_getter_connection = get_method


    # TODO: this should be an ABC
    def pre_build(self):
        pass

    # TODO: this should be an ABC
    def build(self):
        pass

    # TODO: this should be an ABC
    def post_build(self):
        pass

