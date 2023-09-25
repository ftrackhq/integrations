# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore


from ftrack_framework_widget.dialog import FrameworkDialog

from ftrack_qt.widgets.browsers import EntityBrowser


class ChangeContextDialog(FrameworkDialog, EntityBrowser):
    ''' Default Framework change context dialog. '''

    name = 'framework_change_context_dialog'
    ui_type = 'qt'
    docked = False


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
        '''
        Initialize Mixin class change context dialog. It will load the qt dialog and
        mix it with the framework dialog.

        Assumes a host connection is set, if not a warning is issued and the first
        available host is selected by default (standalone test mode().

        *event_manager*: instance of
        :class:`~ftrack_framework_core.event.EventManager`
        *client_id*: Id of the client that initializes the current dialog
        *connect_methods_callback*: Client callback method for the dialog to be
        able to execute client methods.
        *connect_setter_property_callback*: Client callback property setter for
        the dialog to be able to read client properties.
        *connect_getter_property_callback*: Client callback property getter for
        the dialog to be able to write client properties.
        *dialog_options*: Dictionary of arguments passed to configure the
        current dialog.
        '''
        # As a mixing class we have to initialize the parents separately
        FrameworkDialog.__init__(
            self,
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
        )
        EntityBrowser.__init__(
            self,
            None,
            self.session,
            mode=EntityBrowser.MODE_TASK,
            title='CHOOSE TASK (WORKING CONTEXT)',
        )
        print('@@@ host_connection: {}'.format(self.host_connection))

    def connect_focus_signal(self):
        '''Connect signal when the current dialog gets focus'''
        # Update the is_active property.
        QtWidgets.QApplication.instance().focusChanged.connect(
            self._on_focus_changed
        )

    def sync_context(self):
        ''' Always accept new context set elsewhere, should not be possible
        as this should be a modal dialog blocking other UI:s'''
        self._on_client_context_changed_callback()

    def sync_host_connection(self):
        pass

    def _on_client_context_changed_callback(self, event=None):
        '''Client context has been changed'''
        print('@@@ _on_client_context_changed_callback: context_id: {}'.format(self.context_id))
        self.entity_id = self.context_id

    def show_ui(self):
        print('@@@ show_ui'.format())
        if self.exec_():
            self.context_id = self.entity_id

