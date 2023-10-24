# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_qt.framework.dialogs import PublisherDialog


class DefaultPublisherDialog(PublisherDialog):
    '''Default Framework Publisher dialog'''

    name = 'default_publisher_dialog'
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
        super(DefaultPublisherDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )
