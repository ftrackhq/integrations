# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging

from ftrack_framework_core.widget import BaseUI


class FrameworkWidget(BaseUI):
    '''Base class to represent a Widget of the framework'''

    name = None
    widget_type = 'framework_widget'
    dialog_method_connection = None
    dialog_property_getter_connection = None

    @property
    def context_id(self):
        '''Current context id in client'''
        return self._context_id

    @property
    def plugin_config(self):
        '''tool_config of the current plugin'''
        return self._plugin_config

    @property
    def group_config(self):
        '''If plugin lives in a group, return the group tool config'''
        return self._group_config

    @property
    def plugin_name(self):
        '''Name of the current plugin'''
        return self.plugin_config['plugin']

    @property
    def plugin_options(self):
        '''options value of the current plugin'''
        return self._options

    @plugin_options.setter
    def plugin_options(self, value):
        '''
        Updates the options of the current plugin with the given *value*
        '''
        if type(value) != dict:
            return

        self._options.update(value)

        self.on_set_plugin_option(self._options)

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        group_config,
        on_set_plugin_option,
        on_run_ui_hook,
        parent=None,
    ):
        self._context_id = context_id
        self._plugin_config = plugin_config
        self._group_config = group_config
        self._options = {}
        self._ui_hook_result = None

        # Connect dialog methods and properties
        self.on_set_plugin_option = on_set_plugin_option
        self.on_run_ui_hook = on_run_ui_hook

        super(FrameworkWidget, self).__init__(event_manager, client_id, parent)

    def update_context(self, context_id):
        '''Updates the widget context_id with the given *context_id*'''
        self._context_id = context_id
        self.on_context_updated()

    def on_context_updated(self):
        '''Called when context of the widget has been updated.

        Override to handle context change in inheriting class.
        '''
        pass

    def set_plugin_option(self, name, value):
        '''
        Updates the *name* option of the current plugin with the given *value*
        '''
        self.plugin_options = {name: value}

    def validate(self):
        '''Re implement this method to add validation to the widget'''
        return None

    def plugin_run_callback(self, log_item):
        '''
        Receive the callback with the plugin info every time a plugin has been
        executed. *log_item* is the plugin info dictionary.

        NOTE: Make sure this is executed in the QT/DCC main thread as this might be
        called asynchronously.
        '''
        pass

    def run_ui_hook(self, payload):
        '''
        Call the on_run_ui_hook method from the dialog with the given *payload*.
        '''
        self.on_run_ui_hook(payload)

    def ui_hook_callback(self, ui_hook_result):
        '''
        Get the result of the ui_hook method from the plugin, should be overriden
        as needed by the inheriting class.

        NOTE: Make sure this is executed in the QT/DCC main thread as this might be
        called asynchronously.
        '''
        pass

    def populate(self):
        '''Fetch info from plugin to populate the widget'''
        pass

    @classmethod
    def register(cls):
        '''
        Register function to discover widget by class *cls*. Returns False if the
        class is not registerable.
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
            'extension_type': 'widget',
            'name': cls.name,
            'extension': cls,
            'path': inspect.getfile(cls),
        }

        return data
