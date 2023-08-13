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

class Base(object):
    '''Base Class to represent a Plugin'''

    # We Define name, plugin_type and host_type as class variables for
    # convenience for the user when creating its own plugin.
    name = None
    # TODO: framework_dialog and framework_widget for the child classes
    widget_type = 'framework_base'

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
        self._parent = None
        self._is_active = False

        self._client_id = client_id

        # Subscribe to client events
        self._subscribe_client_events()

        self.pre_build()
        self.build()
        self.post_build()
        self.connect_focus_signal()

    def _subscribe_client_events(self):
        pass

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
        pass






