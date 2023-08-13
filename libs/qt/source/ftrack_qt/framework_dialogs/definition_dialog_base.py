# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore


from ftrack_framework_widget.dialog import Dialog

from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.headers import SessionHeader
from ftrack_qt.widgets.selectors import ContextSelector


class DefinitionDialogBase(Dialog, QtWidgets.QDialog):
    '''Base Class to represent a Plugin'''

    name = 'framework_definition_dialog'
    definition_filter = None

    @property
    def filtred_definitions(self):
        definitions = list(self.definitions.values())
        if self.definition_filter:
            definitions = self.definitions[self.definition_filter]
        return definitions

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
        self._context_selector = None
        self._host_connection_selector = None
        self._definition_selector = None
        self._header = None

        QtWidgets.QDialog.__init__(self, parent=parent)
        Dialog.__init__(
            self,
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
        super(DefinitionDialogBase, self).pre_build()
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    # TODO: this should be an ABC
    def build(self):
        super(DefinitionDialogBase, self).build()
        # Create the header
        self._header = SessionHeader(self.session)
        # TODO: implement progress widget. I think client should communicate the
        #  progress to the UI with an ftrack event. And we use the widget dialog
        #  id to identify which widget(or widgets) should be aware of it.
        #self._progress_widget = ProgressWidget
        #self._header.add_widget(self._progress_widget)

        # TODO: we have to update the signals from the context selector to
        #  identify that are our signals and not qt signals.
        self._context_selector = ContextSelector(
            self.session,
            enble_context_change=True
        )
        # Set context from client:
        self._on_client_context_changed_callback()

        self._host_connection_selector = ListSelector("Host Selector")

        self._definition_selector = ListSelector("Definitions")

        # ToDO: add the run definition button

        # TODO: add scroll area where to put the publisher widget.
        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.layout().addWidget(self._header)
        self.layout().addWidget(self._context_selector, QtCore.Qt.AlignTop)
        self.layout().addWidget(self._host_connection_selector)
        self.layout().addWidget(self._definition_selector)
        self.layout().addWidget(self._scroll_area, 100)

    # TODO: this should be an ABC
    def post_build(self):
        super(DefinitionDialogBase, self).post_build()
        # Connect context selector signals
        self._context_selector.context_changed.connect(self._on_context_selected_callback)
        # Connect host selector signals
        self._host_connection_selector.current_item_changed.connect(self._on_host_selected_callback)
        self._host_connection_selector.refresh_clicked.connect(self._on_refresh_hosts_callback)
        # Connect definition selector signals
        self._definition_selector.current_item_changed.connect(self._on_definition_selected_callback)
        self._definition_selector.refresh_clicked.connect(self._on_refresh_definitions_callback)

        # Add host connection items
        self._add_host_connection_items()

    def show(self):
        QtWidgets.QDialog.show(self)
    # TODO: this should be an ABC
    def connect_focus_signal(self):
        # Update the is_active property.
        QtWidgets.QApplication.instance().focusChanged.connect(self._on_focus_changed)

    def _add_host_connection_items(self):
        for host_connection in self.host_connections:
            self._host_connection_selector.add_item(host_connection.host_id)

        # TODO: deactivate the signal momentanetly to avoid re-selecting the host
        if self.host_connection:
            # Prevent the sync calling on creation as host might be already set.
            self._on_client_host_changed_callback()

    def _add_definition_items(self):
        if not self.host_connection:
            return
        for definition_list in self.filtred_definitions:
            for definition in definition_list:
                self._definition_selector.add_item(definition.name)

    def _on_context_selected_callback(self, context_id):
        if not context_id:
            return
        if self.context_id != context_id:
            self.context_id = context_id

    def _on_host_selected_callback(self, item_text):
        '''
        Get the definition with the given *item* name from the filtered definitions
        '''
        if not item_text:
            return
        self._definition_selector.clear_items()
        match = False
        if self.host_connection != item_text:
            for host_connection in self.host_connections:
                if host_connection.host_id == item_text:
                    self.host_connection = host_connection
                    match = True
                    break
        else:
            match = True

        if match:
            self._add_definition_items()

    def _on_refresh_hosts_callback(self):
        self._definition_selector.clear_items()
        self.host_connection = None
        self._host_connection_selector.clear_items()
        self.client_method_connection('discover_hosts')
        self._add_host_connection_items()

    def _on_definition_selected_callback(self, item_text):
        '''
        Get the definition with the given *item* name from the filtered definitions
        '''
        if self.definition:
            if self.definition.name == item_text:
                return
        definition = None
        for definition_list in self.filtred_definitions:
            definition = definition_list.get_first(name=item_text)
            if definition:
                break
        if definition:
            self.definition = definition

    def _on_refresh_definitions_callback(self):
        # TODO: double think if definitions can be refreshed? maybe we should
        #  thn re-select the same host instead of discovering hosts again?
        self.definition = None
        self._definition_selector.clear_items()
        # TODO: evealuate if this should be an event,
        #  like client_run_method_topic where we pass the method,
        #  arguments and callback. In that case we will need to pass a client id.
        self.client_method_connection('discover_hosts')
        self._add_definition_items()

    def _on_client_context_changed_callback(self, event=None):
        self._context_selector.context_id = self.context_id
        print(self._context_selector.is_browsing)

    # TODO: This should be an ABC
    def _on_client_hosts_discovered_callback(self, event=None):
        # TODO: for host_id in host_connection if host_id not in host_selector items, add it.
        pass

    # TODO: This should be an ABC
    def _on_client_host_changed_callback(self, event=None):
        if (
                self._host_connection_selector.current_item_text() !=
                self.host_connection.host_id
        ):
            self._host_connection_selector.set_current_item(
                self.host_connection.host_id
            )

    # TODO: This should be an ABC
    def _on_client_definition_changed_callback(self, event=None):
        print("_on_client_definition_changed_callback" )
        definition_name = None
        if self.definition:
            definition_name = self.definition.name
        if (
                self._definition_selector.current_item_index() in [0, -1] and
                not definition_name
        ):
            return
        if (
                self._definition_selector.current_item_text() !=
                definition_name
        ):
            self._definition_selector.set_current_item(
                definition_name
            )

    # TODO: This should be an ABC
    def sync_context(self):
        if self._context_selector.is_browsing:
            return
        if self.context_id != self._context_selector.context_id:
            result = self.show_message_dialog(
                title='Context out of sync!',
                message='Selected context is not the current context, '
                        'do you want to update UI to syc with the current context?',
                button_1_text='Update',
                button_2_text='Keep Current'
            )
            if result == 1:
                self._on_client_context_changed_callback()
            elif result == 0:
                # TODO: missing the on conecxt selection changed. Update this oonce added.
                self.context_id = self._context_selector.context_id

    # TODO: This should be an ABC
    def sync_host_connection(self):
        if (
                not self.host_connection.host_id and
                self._host_connection_selector.current_item_index() not in [0,-1]
        ):
            return
        if self.host_connection.host_id != self._host_connection_selector.current_item_text():
            result = self.show_message_dialog(
                title='Host connection out of sync!',
                message='Selected host connection is not the current host_connection, '
                        'do you want to update UI to syc with the current one?',
                button_1_text='Update',
                button_2_text='Keep Current'
            )
            if result == 1:
                self._on_client_host_changed_callback()
            elif result == 0:
                self._on_host_selected_callback(
                    self._host_connection_selector.current_item_text()
                )

    # TODO: This should be an ABC
    def sync_definition(self):
        sync = False
        if not self.definition:
            if self._definition_selector.current_item_index() not in [0,-1]:
                sync = True
        else:
            if self.definition.name != self._definition_selector.current_item_text():
                match = False
                for definition_list in self.filtred_definitions:
                    definition = definition_list.get_first(name=self.definition.name)
                    if definition:
                        match = True
                        break
                if not match:
                    # Automatically sync current definition to client as the current
                    # definition is not available for this UI.
                    self._on_definition_selected_callback(
                        self._definition_selector.current_item_text()
                    )
                    return
                if match:
                    sync = True
        if sync:
            result = self.show_message_dialog(
                title='Current definition is out of sync!',
                message='Selected definition is not the current definition, '
                        'do you want to update UI to syc with the current one?',
                button_1_text='Update',
                button_2_text='Keep Current'
            )
            if result == 1:
                self._on_client_definition_changed_callback()
            elif result == 0:
                self._on_definition_selected_callback(
                    self._definition_selector.current_item_text()
                )


    # TODO: maybe move this to a utils and standarize icon.
    def show_message_dialog(self, title, message, button_1_text, button_2_text):
        message_box = QtWidgets.QMessageBox()
        message_box.setWindowTitle(title)
        message_box.setText(message)
        message_box.setIcon(QtWidgets.QMessageBox.Question)
        message_box.addButton(button_1_text, QtWidgets.QMessageBox.YesRole)
        message_box.addButton(button_2_text, QtWidgets.QMessageBox.NoRole)
        result = message_box.exec_()
        return result
