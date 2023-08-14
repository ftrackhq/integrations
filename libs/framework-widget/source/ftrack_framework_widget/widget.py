# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import uuid

from ftrack_framework_widget import Base, active_widget


class Widget(Base):
    '''Base Class to represent a Plugin'''

    # We Define name, plugin_type and host_type as class variables for
    # convenience for the user when creating its own plugin.
    name = None
    widget_type = 'framework_widget'
    dialog_run_plugin_method_connection = None

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
            plugin_definition,
            dialog_run_plugin_method_callback,
            parent=None
    ):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        super(Widget, self).__init__(
            event_manager,
            client_id,
            parent
        )
        self._plugin_definition = plugin_definition
        # Augment definition with the widget ID:
        self.plugin_definition.id = self.id

        self.connect_methods(dialog_run_plugin_method_callback)

    def connect_methods(self, method):
        # TODO: should this be subscription events?
        self.dialog_run_plugin_method_connection = method

    # TODO: this should be an ABC
    def pre_build(self):
        pass

    # TODO: this should be an ABC
    def build(self):
        pass

    # TODO: this should be an ABC
    def post_build(self):
        pass

    def run_plugin_method(self, plugin_method):
        self.dialog_run_plugin_method_connection(
            self.plugin_definition,
            plugin_method,
            self.id
        )

    # TODO: this should be an ABC
    def run_plugin_callback(self, plugin_info):
        # Called by the dialog
        executed_method = plugin_info['plugin_method']
        method_result = plugin_info['plugin_method_result']
        print('executed_method'.format(executed_method))
        print('method_result'.format(method_result))
        # TODO: Implement this as you want in each widget.


