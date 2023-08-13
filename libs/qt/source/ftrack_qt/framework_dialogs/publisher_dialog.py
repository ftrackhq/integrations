# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore


from ftrack_qt.framework_dialogs import DefinitionDialogBase


class PublisherDialog(DefinitionDialogBase):
    '''Base Class to represent a Plugin'''

    name = 'framework_publisher_dialog'
    definition_filter = ['publisher']

    def __init__(
            self,
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=None
    ):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        super(PublisherDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent
        )

    # TODO: this should be an ABC
    def pre_build(self):
        super(PublisherDialog, self).pre_build()

    # TODO: this should be an ABC
    def build(self):
        super(PublisherDialog, self).build()

    # TODO: this should be an ABC
    def post_build(self):
        super(PublisherDialog, self).post_build()


