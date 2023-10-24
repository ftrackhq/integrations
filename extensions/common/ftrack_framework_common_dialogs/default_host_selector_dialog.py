# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_qt.dialogs import HostSelectorDialog


class DefaultHostSelectorDialog(HostSelectorDialog):
    '''Default Framework Publisher dialog'''

    name = 'default_host_selector_dialog'
    tool_config_type_filter = ['publisher']
    ui_type = 'qt'
    docked = True

    def __init__(
        self,
        event_manager,
        client_id,
        connect_methods_callback,
        connect_setter_property_callback,
        connect_getter_property_callback,
        dialog_options,
        parent=None,
    ):
        ''' '''
        super(DefaultHostSelectorDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )
