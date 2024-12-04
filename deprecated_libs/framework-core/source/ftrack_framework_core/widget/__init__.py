# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging


def active_widget(func):
    def wrapper(self, *args, **kwargs):
        '''If self.active in class execute the function'''
        if self.is_active:
            return func(self, *args, **kwargs)

    return wrapper


# Docstring this class
class BaseUI(object):
    '''Base Class to represent a Plugin'''

    name = None
    widget_type = 'framework_ui_base'
    ui_type = 'all'

    def __repr__(self):
        return '<{}>'.format(self.name)

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

    def __init__(self, event_manager, client_id, parent=None):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        self._event_manager = event_manager

        # Set properties to 0
        self._is_active = False

        self._client_id = client_id
        self._parent = parent

        # Subscribe to client events
        self._subscribe_client_events()

        self.connect_focus_signal()

    def _subscribe_client_events(self):
        '''Make the dialog subscribe to client events'''
        pass

    def show_ui(self):
        pass

    def connect_focus_signal(self):
        # TODO: Find a way to simulate a pyside connection, so every time that
        #  show_ui() is called, we connect it to on_focus_changed
        pass

    def change_focus(self, old_widget, new_widget):
        self._on_focus_changed(old_widget, new_widget)

    def _on_focus_changed(self, old_widget, new_widget):
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

    @classmethod
    def register(cls):
        '''
        Register function to discover widget by class *cls*. Returns False if the
        class is not registrable.
        '''
        import inspect

        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )
        logger.debug(
            'registering: {} for {}'.format(cls.name, cls.widget_type)
        )

        if not hasattr(cls, 'name') or not cls.name:
            # Can only register widgets that have a name, not base classes
            logger.warning(
                "Can only register widgets that have a name, no name provided "
                "for this one"
            )
            return False

        data = {
            'extension_type': 'base_framework_widget',
            'name': cls.name,
            'extension': cls,
            'path': inspect.getfile(cls),
        }

        return data
