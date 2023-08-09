# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_widget import BaseWidget


class FrameworkDialog(BaseWidget):
    '''Base Class to represent a Plugin'''

    # We Define name, plugin_type and host_type as class variables for
    # convenience for the user when creating its own plugin.
    name = None
    widget_type = 'framework_dialog'

    @property
    def definitions(self):
        '''
        Dependency framework widgets
        '''
        return self.client_property_getter_connection('definitions')

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

        super(FrameworkDialog, self).__init__(
            event_manager,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            parent
        )
        self._definitions = None

    # TODO: this should be an ABC
    def pre_build(self):
        pass

    # TODO: this should be an ABC
    def build(self):
        pass

    # TODO: this should be an ABC
    def post_build(self):
        pass



