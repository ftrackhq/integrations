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

    def __init__(self, event_manager):
        '''
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        super(FrameworkDialog, self).__init__(event_manager)
        self._definition_selector = None

    # TODO: this should be an ABC
    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        pass

    # TODO: this should be an ABC
    def build(self):
        self._definition_selector = ListSelector()
        self._add_definition_items()

    def _add_definition_items(self):
        definitions = list(self.definitions.values())
        if self.definition_filter:
            definitions = self.definitions[self.definition_filter]

        for definition_list in definitions:
            for definition in definition_list:
                self._definition_selector.add_item(definition.name)


    # TODO: this should be an ABC
    def post_build(self):
        self._definition_selector.current_index_changed.connect(self._on_definition_selected_callback)
        self._definition_selector.refresh_clicked.connect(self._on_refresh_definitions_callback)

    def _on_definition_selected_callback(self, item):
        self.definition = self.definitions[item]

    def _on_refresh_definitions_callback(self):
        pass

