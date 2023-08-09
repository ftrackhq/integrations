# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore


from ftrack_framework_widget.framework_dialog import FrameworkDialog
from ftrack_qt.widgets.selectors import ListSelector


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
        self._definition_selector = ListSelector()
        self._definition_selector.label = "All Definitions"
        self._add_definition_items()

        self.layout().addWidget(self._definition_selector)

    def _add_definition_items(self):
        for definition_list in self.filtred_definitions:
            for definition in definition_list:
                self._definition_selector.add_item(definition.name)


    # TODO: this should be an ABC
    def post_build(self):
        super(FrameworkDefinitionDialog, self).post_build()
        self._definition_selector.current_item_changed.connect(self._on_definition_selected_callback)
        self._definition_selector.refresh_clicked.connect(self._on_refresh_definitions_callback)

    def _on_definition_selected_callback(self, item):
        definition = None
        for definition_list in self.filtred_definitions:
            definition = definition_list.get_first(name=item)
            if definition:
                break
        self.definition = definition

    def _on_refresh_definitions_callback(self):
        self.definition = None
        self._definition_selector.clear_items()
        # TODO: evealuate if this should be an event,
        #  like client_run_method_topic where we pass the method,
        #  arguments and callback. In that case we will need to pass a client id.
        self.client_method_connection('discover_hosts')
        self._add_definition_items()

