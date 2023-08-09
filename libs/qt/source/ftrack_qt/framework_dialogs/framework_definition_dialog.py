# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore


from ftrack_framework_widget.framework_dialog import FrameworkDialog

from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.headers import SessionHeader


class FrameworkDefinitionDialog(FrameworkDialog, QtWidgets.QDialog):
    '''Base Class to represent a Plugin'''

    name = 'framework_definition_dialog'
    definition_filter = None

    @property
    def definition_selector(self):
        return self._definition_selector

    @property
    def filtred_definitions(self):
        definitions = list(self.definitions.values())
        if self.definition_filter:
            definitions = self.definitions[self.definition_filter]
        return definitions

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
        self._definition_selector = None
        self._header = None

        QtWidgets.QDialog.__init__(self, parent=parent)
        FrameworkDialog.__init__(
            self,
            event_manager,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            parent
        )

    # TODO: this should be an ABC
    def pre_build(self):
        super(FrameworkDefinitionDialog, self).pre_build()
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    # TODO: this should be an ABC
    def build(self):
        super(FrameworkDefinitionDialog, self).build()
        # Create the header
        self._header = SessionHeader(self.session)
        # TODO: implement progress widget. I think client should communicate the
        #  progress to the UI with an ftrack event. And we use the widget dialog
        #  id to identify which widget(or widgets) should be aware of it.
        #self._progress_widget = ProgressWidget
        #self._header.add_widget(self._progress_widget)

        self._host_connection_selector = ListSelector("Host Selector")
        # TODO: Add the host selector
        # TODO: add the context selector

        self._definition_selector = ListSelector("Definitions")
        self._add_definition_items()

        # TODO: add scroll area where to put the publisher widget.

        self.layout().addWidget(self._definition_selector)

    def _add_host_connection_items(self):
        for host_connection in self.host_connections:
            self._host_connection_selector.add_item(host_connection.id)

    def _add_definition_items(self):
        for definition_list in self.filtred_definitions:
            for definition in definition_list:
                self._definition_selector.add_item(definition.name)

    # TODO: this should be an ABC
    def post_build(self):
        super(FrameworkDefinitionDialog, self).post_build()
        # Connect host selector signals
        self._host_connection_selector.current_item_changed.connect(self._on_host_selected_callback)
        self._host_connection_selector.refresh_clicked.connect(self._on_refresh_hosts_callback)
        # Connect definition selector signals
        self._definition_selector.current_item_changed.connect(self._on_definition_selected_callback)
        self._definition_selector.refresh_clicked.connect(self._on_refresh_definitions_callback)

    def _on_host_selected_callback(self, item):
        '''
        Get the definition with the given *item* name from the filtered definitions
        '''
        for host_connection in self.host_connections:
            if host_connection.id == item:
                self.host_connection = host_connection

    def _on_refresh_hosts_callback(self):
        self.host_connection = None
        self._host_connection_selector.clear_items()
        self._definition_selector.clear_items()
        self.client_method_connection('discover_hosts')
        self._add_host_connection_items()

    def _on_definition_selected_callback(self, item):
        '''
        Get the definition with the given *item* name from the filtered definitions
        '''
        definition = None
        for definition_list in self.filtred_definitions:
            definition = definition_list.get_first(name=item)
            if definition:
                break
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

