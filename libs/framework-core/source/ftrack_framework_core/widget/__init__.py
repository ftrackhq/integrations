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
    client_method_connection = None
    client_property_setter_connection = None
    client_property_getter_connection = None
    tool_config_type_filter = None

    def __repr__(self):
        return '<{}>'.format(self.name)

    @property
    def id(self):
        '''
        Id of the widget
        '''
        return self._id

    # Ftrack Connection properties
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

    # QT Widget properties
    @property
    def parent(self):
        return self._parent

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

    @property
    def framework_widgets(self):
        '''Return instanced framework widgets'''
        return self.__instanced_widgets

    # Client connection properties
    @property
    def client_id(self):
        return self._client_id

    @property
    def context_id(self):
        '''
        Current context id in client
        '''
        return self.client_property_getter_connection('context_id')

    @context_id.setter
    def context_id(self, value):
        '''
        Set the *value* as current context id in client
        '''
        self.client_property_setter_connection('context_id', value)

    @property
    def host_connection(self):
        '''
        Current host connection in client
        '''
        return self.client_property_getter_connection('host_connection')

    @host_connection.setter
    def host_connection(self, value):
        '''
        Set the *value* as current host_connection id in client
        '''
        self.client_property_setter_connection('host_connection', value)

    @property
    def host_connections(self):
        '''
        Available host_connections in client
        '''
        return self.client_property_getter_connection('host_connections')

    @property
    def registry(self):
        '''Return discovered framework widgets from client'''
        return self.client_property_getter_connection('registry')

    # Tool Config properties
    @property
    def tool_configs(self):
        '''
        Available tool_configs in client
        '''
        return self.client_property_getter_connection('tool_configs')

    @property
    def filtered_tool_configs(self):
        '''
        Return tool_configs of types that match the tool_config_type_filter
        '''
        # TODO: maybe move this to an utility?
        if not self.tool_config_type_filter:
            return list(self.tool_configs.values())
        tool_configs = {}
        for tool_config_type in self.tool_config_type_filter:
            tool_configs[tool_config_type] = self.tool_configs.get(
                tool_config_type
            )
        return tool_configs

    @property
    def tool_config(self):
        '''Returns the current selected tool_config.'''
        return self._tool_config

    @tool_config.setter
    def tool_config(self, value):
        '''
        Set the given *value* as tool_config if value.name found in
        self.tool_configs
        '''

        if value and not get_tool_config_by_name(
            self.tool_configs[value['config_type']], value['name']
        ):
            self.logger.error(
                "Invalid tool_config, choose one from : {}".format(
                    self.tool_configs
                )
            )
            return

        if value:
            # Get plugins from tool_config
            plugins = get_plugins(value, names_only=True)

            unregistered_plugins = self.client_method_connection(
                'verify_plugins', arguments={"plugin_names": plugins}
            )
            if unregistered_plugins:
                raise Exception(
                    f"Unregistered plugins found: {unregistered_plugins}"
                    f"\n Please make sure plugins are in the extensions path"
                )

        self._tool_config = value

        if self._tool_config:
            arguments = {
                "tool_config_reference": self._tool_config['reference'],
                "item_reference": None,
                "options": self.dialog_options,
            }
            self.client_method_connection(
                'set_config_options', arguments=arguments
            )

        # Call _on_tool_config_changed_callback to let the UI know that a new
        # tool_config has been set.
        self._on_tool_config_changed_callback()

    @property
    def tool_config_options(self):
        '''
        Current tool_config_options in client
        '''
        return self.client_property_getter_connection('tool_config_options')

    @property
    def dialog_options(self):
        # TODO: review how the dialog options work do we need them?
        '''Return dialog options as passed on from client'''
        return self._dialog_options or {}

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
