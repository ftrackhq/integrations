# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging

from ftrack_framework_widget import BaseUI, active_widget


class FrameworkWidget(BaseUI):
    '''Base class to represent a Widget of the framework'''

    # We Define name, plugin_type and host_type as class variables for
    # convenience for the user when creating its own plugin.
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
    def plugin_name(self):
        '''Name of the current plugin'''
        return self.plugin_config.plugin_name

    @property
    def plugin_context_data(self):
        '''context_data value of the current plugin'''
        return self.plugin_config.context_data

    @plugin_context_data.setter
    def plugin_context_data(self, value):
        '''
        Updates the context_data of the current plugin with the given *value*
        '''
        if type(value) != dict:
            return
        self.plugin_config.context_data.update(value)

    @property
    def plugin_data(self):
        '''data value of the current plugin'''
        return self.plugin_config.data

    @plugin_data.setter
    def plugin_data(self, value):
        '''
        Updates the data of the current plugin with the given *value*
        '''
        if type(value) != dict:
            return
        self.plugin_config.data.update(value)

    @property
    def plugin_options(self):
        '''options value of the current plugin'''
        return self.plugin_config.options

    @plugin_options.setter
    def plugin_options(self, value):
        '''
        Updates the options of the current plugin with the given *value*
        '''
        if type(value) != dict:
            return
        self.plugin_config.options.update(value)

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        dialog_connect_methods_callback,
        dialog_property_getter_connection_callback,
        parent=None,
    ):
        self._context_id = context_id
        self._plugin_config = plugin_config

        # Connect dialog methods and properties
        self.connect_methods(dialog_connect_methods_callback)
        self.connect_properties(dialog_property_getter_connection_callback)

        super(FrameworkWidget, self).__init__(event_manager, client_id, parent)

        # Augment tool_config with the widget ID:
        self.plugin_config.widget_id = self.id

    def connect_methods(self, method):
        '''
        Connect the dialog callback method for the widget to be able to execute
        dialog methods.
        '''
        self.dialog_method_connection = method

    def connect_properties(self, get_method):
        '''
        Connect the dialog getterproperties for the widget to be
        able to call them.
        '''
        self.dialog_property_getter_connection = get_method

    def update_context(self, context_id):
        '''Updates the widget context_id with the given *context_id*'''
        self._context_id = context_id
        self.on_context_updated()

    def run_plugin_method(self, plugin_method_name):
        '''
        Call the run_plugin_method from the dialog with the current
        plugin_config, id and the given *plugin_method_name* as arguments
        '''
        arguments = {
            "plugin_config": self.plugin_config,
            "plugin_method_name": plugin_method_name,
            'plugin_widget_id': self.id,
        }
        self.dialog_method_connection('run_plugin_method', arguments=arguments)

    def run_plugin_callback(self, plugin_info):
        '''
        Called when a result of an executed plugin is published. It provides
        the *plugin_info*
        '''
        # Called by the dialog
        executed_method = plugin_info['plugin_method']
        method_result = plugin_info['plugin_method_result']
        print('executed_method'.format(executed_method))
        print('method_result'.format(method_result))
        raise NotImplementedError(
            "This method should be implemented by the inheriting class"
        )

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

    @classmethod
    def register(cls):
        '''
        Register function to discover widget by class *cls*. Returns False if the
        class is not registerable.
        '''
        if not hasattr(cls, 'name') or not cls.name:
            # Can only register widgets that have a name, not base classes
            return False

        logger = logging.getLogger(
            '{0}.{1}'.format(__name__, cls.__class__.__name__)
        )
        logger.debug(
            'registering: {} for {}'.format(cls.name, cls.widget_type)
        )

        data = {'extension_type': 'widget', 'name': cls.name, 'cls': cls}

        return data
