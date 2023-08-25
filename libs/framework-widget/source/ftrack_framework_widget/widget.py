# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import uuid

from ftrack_framework_widget import BaseUI, active_widget


# TODO: docstring this code
class FrameworkWidget(BaseUI):
    '''Base Class to represent a Widget of the framework'''

    # We Define name, plugin_type and host_type as class variables for
    # convenience for the user when creating its own plugin.
    name = None
    widget_type = 'framework_widget'
    dialog_method_connection = None
    dialog_property_getter_connection = None

    @property
    def context_id(self):
        return self._context_id

    @property
    def plugin_definition(self):
        return self._plugin_definition

    @property
    def plugin_name(self):
        return self.plugin_definition.plugin

    @property
    def plugin_context_data(self):
        return self.plugin_definition.context_data

    @plugin_context_data.setter
    def plugin_context_data(self, value):
        if type(value) != dict:
            return
        self.plugin_definition.context_data.update(value)

    @property
    def plugin_data(self):
        return self.plugin_definition.data

    @plugin_data.setter
    def plugin_data(self, value):
        if type(value) != dict:
            return
        self.plugin_definition.data.update(value)

    @property
    def plugin_options(self):
        return self.plugin_definition.options

    @plugin_options.setter
    def plugin_options(self, value):
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

        self.connect_methods(dialog_connect_methods_callback)
        self.connect_properties(dialog_property_getter_connection_callback)

        super(FrameworkWidget, self).__init__(event_manager, client_id, parent)

        # Augment definition with the widget ID:
        self.plugin_definition.widget_id = self.id

    def connect_methods(self, method):
        self.dialog_method_connection = method

    def connect_properties(self, get_method):
        self.dialog_property_getter_connection = get_method

    # TODO: this should be an ABC
    def pre_build(self):
        pass

    # TODO: this should be an ABC
    def build(self):
        pass

    # TODO: this should be an ABC
    def post_build(self):
        pass

    # TODO: this should be an ABC
    def show(self):
        pass

    def update_context(self, context_id):
        self._context_id = context_id
        self.on_context_updated()

    def run_plugin_method(self, plugin_method_name):
        arguments = {
            "plugin_definition": self.plugin_definition,
            "plugin_method_name": plugin_method_name,
            'plugin_widget_id': self.id,
        }
        self.dialog_method_connection('run_plugin_method', arguments=arguments)

    # TODO: this should be an ABC
    def run_plugin_callback(self, plugin_info):
        # Called by the dialog
        executed_method = plugin_info['plugin_method']
        method_result = plugin_info['plugin_method_result']
        print('executed_method'.format(executed_method))
        print('method_result'.format(method_result))

    # TODO: this should be an ABC
    def on_context_updated(self):
        pass

    def set_plugin_option(self, name, value):
        self.plugin_options = {name: value}
