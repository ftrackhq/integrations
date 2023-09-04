# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

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
    def plugin_definition(self):
        '''Definition of the current plugin'''
        return self._plugin_definition

    @property
    def plugin_name(self):
        '''Name of the current plugin'''
        return self.plugin_definition.plugin

    @property
    def plugin_context_data(self):
        '''context_data value of the current plugin'''
        return self.plugin_definition.context_data

    @plugin_context_data.setter
    def plugin_context_data(self, value):
        '''
        Updates the context_data of the current plugin with the given *value*
        '''
        if type(value) != dict:
            return
        self.plugin_definition.context_data.update(value)

    @property
    def plugin_data(self):
        '''data value of the current plugin'''
        return self.plugin_definition.data

    @plugin_data.setter
    def plugin_data(self, value):
        '''
        Updates the data of the current plugin with the given *value*
        '''
        if type(value) != dict:
            return
        self.plugin_definition.data.update(value)

    @property
    def plugin_options(self):
        '''options value of the current plugin'''
        return self.plugin_definition.options

    @plugin_options.setter
    def plugin_options(self, value):
        '''
        Updates the options of the current plugin with the given *value*
        '''
        if type(value) != dict:
            return
        self.plugin_definition.options.update(value)

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_definition,
        dialog_connect_methods_callback,
        dialog_property_getter_connection_callback,
        parent=None,
    ):
        self._context_id = context_id
        self._plugin_definition = plugin_definition

        # Connect dialog methods and properties
        self.connect_methods(dialog_connect_methods_callback)
        self.connect_properties(dialog_property_getter_connection_callback)

        super(FrameworkWidget, self).__init__(event_manager, client_id, parent)

        # Augment definition with the widget ID:
        self.plugin_definition.widget_id = self.id

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

    # TODO: this should be an ABC
    def show_ui(self):
        '''
        To be overriden by the implemented widget. Should show the widget:
        Pseudocode example PySide UI:
        self.show()
        '''
        pass

    def update_context(self, context_id):
        '''Updates the widget context_id with the given *context_id*'''
        self._context_id = context_id
        self.on_context_updated()

    def run_plugin_method(self, plugin_method_name):
        '''
        Call the run_plugin_method from the dialog with the current
        plugin_definition, id and the given *plugin_method_name* as arguments
        '''
        arguments = {
            "plugin_definition": self.plugin_definition,
            "plugin_method_name": plugin_method_name,
            'plugin_widget_id': self.id,
        }
        self.dialog_method_connection('run_plugin_method', arguments=arguments)

    # TODO: this should be an ABC
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

    # TODO: this should be an ABC
    def on_context_updated(self):
        '''Called when context of the widget has been updated'''
        pass

    def set_plugin_option(self, name, value):
        '''
        Updates the *name* option of the current plugin with the given *value*
        '''
        self.plugin_options = {name: value}
