# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import uuid


def active_widget(func):
    def wrapper(self, *args, **kwargs):
        '''If self.active in class execute the function'''
        print ("Gettting the variable self.active from class".format(self.active))
        if self.active:
            return func(self, *args, **kwargs)
    return wrapper

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

    @property
    def client_id(self):
        return self._client_id

    @property
    def is_active(self):
        '''
        Dependency framework widgets
        '''
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        '''
        Dependency framework widgets
        '''
        self._is_active = value

    def __init__(
            self,
            event_manager,
            client_id,
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
        self._is_active = False

        self._client_id = client_id
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
        self.connect_focus_signal()

    def connect_methods(self, method):
        # TODO: should this be subscription events?
        self.client_method_connection = method

    def connect_properties(self, set_method, get_method):
        # TODO: should this be subscription events?
        self.client_property_setter_connection = set_method
        self.client_property_getter_connection = get_method

    def _subscribe_client_events(self):
        self.event_manager.subscribe.client_signal_context_changed(
            self.client_id,
            callback=self._on_client_context_changed_callback
        )
        self.event_manager.subscribe.client_signal_hosts_discovered(
            self.client_id,
            callback=self._on_client_hosts_discovered_callback
        )
        self.event_manager.subscribe.client_signal_host_changed(
            self.client_id,
            callback=self._on_client_host_changed_callback
        )
        # TODO: I think this one is not needed as when host is changed new definitions are discovered. And if context id is changed also new definitions are discovered.
        # self.event_manager.subscribe.client_notify_definitions_discovered(
        #     self.client_id,
        #     callback=self._on_client_context_changed_callback
        # )
        self.event_manager.subscribe.client_signal_definition_changed(
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

    # TODO: This should be an ABC
    @active_widget
    def _on_client_context_changed_callback(self, event=None):
        '''Will only run if the widget is active'''
        # TODO: carefully, here we should update definitions!
        pass

    # TODO: This should be an ABC
    @active_widget
    def _on_client_hosts_discovered_callback(self, event=None):
        pass

    # TODO: This should be an ABC
    @active_widget
    def _on_client_host_changed_callback(self, event=None):
        # TODO: carefully, here we should update definitions!
        pass

    # TODO: This should be an ABC
    @active_widget
    def _on_client_definition_changed_callback(self, event=None):
        pass

    # TODO: This should be an ABC
    def show(self):
        # TODO: Find a way to simulate a pyside signal
        pass
        #self._on_focus_changed(None, self)

    # TODO: This should be an ABC
    def connect_focus_signal(self):
        # TODO: Find a way to simulate a pyside connection, so every time that
        #  show() is called, we connect it to on_focus_changed
        pass

    def change_focus(self, old_widget, new_widget):
        self._on_focus_changed(old_widget, new_widget)

    def _on_focus_changed(self, old_widget, new_widget):
        if self == old_widget:
            self.is_active = False
        elif self == new_widget:
            self.is_active = True
        else:
            self.is_active = False
        if self.is_active:
            # Syncronize context with client
            self.sync_context()
            # Syncronize Host connection with client
            self.sync_host_connection()
            # Syncronize definitiion with client
            self.sync_definition()

    # TODO: this should be an ABC
    def sync_context(self):
        '''
        Check if selected UI context_id is not sync with the client and sync them.
        Pseudo code example PySide UI:
            if self.context_id not is self.context_Selector.current_text():
                raise confirmation widget to decide which one to keep
                equal self.context_Selector.current_text() to self.context_id or
                the other way around depending on the confirmation widget response
        '''
        pass

    # TODO: this should be an ABC
    def sync_host_connection(self):
        '''
        Check if UI selected host_connection is not sync with the client and sync them.
        '''
        pass

    # TODO: this should be an ABC
    def sync_definition(self):
        '''
        Check if UI selected definition is not sync with the client and sync them.
        We usually want to keep the selected Definition
        '''
        pass




