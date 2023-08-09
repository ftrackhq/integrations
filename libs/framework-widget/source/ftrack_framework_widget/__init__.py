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
    def definitions(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('definitions')

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
    def context_id(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('context_id')

    @context_id.setter
    def context_id(self, value):
        '''
        Dependency framework widgets
        '''
        self.client_property_setter_connection('context_id', value)

    @property
    def host_connection(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('host_connection')

    @host_connection.setter
    def host_connection(self, value):
        '''
        Dependency framework widgets
        '''
        self.client_property_setter_connection('host_connection', value)

    @property
    def host_connections(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('host_connections')
    @property
    def plugins(self):
        '''
        Dependency framework widgets
        '''
        if not self.definition:
            self.logger.warning("Please set a definition before quering plugins")
            return None
        return self.definition.get_all(category='plugin')

    @property
    def parent(self):
        return self._parent

    def __init__(
            self,
            event_manager,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            parent=None
    ):
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
        self._definitions = None
        self._host_connections = None
        self._definition = None
        self._host_connection = None
        self._parent = None

        # tDO: can this be events???? Will be much cleaner
        self.connect_methods(connect_methods_callback)
        self.connect_properties(
            connect_setter_property_callback,
            connect_getter_property_callback
        )

        self._subscribe_client_events()

        self.pre_build()
        self.build()
        self.post_build()

    def connect_methods(self, method):
        # TODO: should this be subscription events?
        self.client_method_connection = method

    def connect_properties(self, set_method, get_method):
        # TODO: should this be subscription events?
        self.client_property_setter_connection = set_method
        self.client_property_getter_connection = get_method

    def _subscribe_client_events(self):
        self.event_manager.subscribe.client_notify_context_changed(
            self.client_id,
            callback=self._on_client_context_changed_callback
        )
        self.event_manager.subscribe.client_notify_hosts_discovered(
            self.client_id,
            callback=self._on_client_hosts_discovered_callback
        )
        self.event_manager.subscribe.client_notify_host_changed(
            self.client_id,
            callback=self._on_client_host_changed_callback
        )
        # TODO: I think this one is not needed as when host is changed new definitions are discovered. And if context id is changed also new definitions are discovered.
        # self.event_manager.subscribe.client_notify_definitions_discovered(
        #     self.client_id,
        #     callback=self._on_client_context_changed_callback
        # )
        self.event_manager.subscribe.client_notify_definition_changed(
            self.client_id,
            callback=self._on_client_definition_changed_callback
        )


    # TODO: this should be an ABC
    def pre_build(self):
        pass

    # TODO: this should be an ABC
    def build(self):
        pass

    # TODO: this should be an ABC
    def post_build(self):
        pass

    def _on_client_context_changed_callback(self):
        # TODO: carefully, here we should update definitions!
        pass

    def _on_client_hosts_discovered_callback(self):
        pass

    def _on_client_host_changed_callback(self):
        # TODO: carefully, here we should update definitions!
        pass

    def _on_client_definition_changed_callback(self):
        pass


