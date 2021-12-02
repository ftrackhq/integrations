import logging
from functools import partial

from Qt import QtWidgets, QtCore


class DefinitionItem(QtWidgets.QPushButton):

    @property
    def definition(self):
        return self._definition

    def __init__(self, text, definition_item, parent=None):
        super(DefinitionItem, self).__init__(text, parent=parent)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self._definition = definition_item
        self.setMinimumWidth(80)


class DefinitionSelector(QtWidgets.QWidget):
    '''DefinitionSelector Base Class'''
    definition_changed = QtCore.Signal(object, object)
    host_changed = QtCore.Signal(object)

    @property
    def selected_host_connection(self):
        return self.host_combobox.itemData(
            self.host_combobox.currentIndex()
        )

    def __init__(self, parent=None):
        '''Initialize DefinitionSelector widget'''
        super(DefinitionSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.host_connection = None
        self.schemas = None
        self.definition_filter = None
        self.definitions = []

        self.host_connections = []
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        self.host_combobox = QtWidgets.QComboBox()
        self.definition_combobox = QtWidgets.QComboBox()

        self.layout().addWidget(self.host_combobox)
        self.layout().addWidget(self.definition_combobox)

        self.host_combobox.addItem('- Select host -')

    def post_build(self):
        '''Connect the widget signals'''
        self.host_combobox.currentIndexChanged.connect(self._on_change_host)
        self.definition_combobox.currentIndexChanged.connect(
            self._on_select_definition
        )

    def change_host_index(self, index):
        self.host_combobox.setCurrentIndex(index)

    def _on_change_host(self, index):
        '''triggered when chaging host selection to *index*'''
        self.definition_combobox.clear()
        self.host_connection = self.host_combobox.itemData(index)
        self.host_changed.emit(self.host_connection)

        if not self.host_connection:
            self.logger.debug('No data for selected host')
            return

        self.schemas = [
            schema for schema in self.host_connection.definitions['schema']
            if schema.get('title').lower() != 'package'
        ]

        self._populate_definitions()

    def _populate_definitions(self):
        self.definition_combobox.addItem('- Select Definition -')
        self.definitions=[]
        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self.definition_filter:
                if schema_title != self.definition_filter:
                    continue
            items = self.host_connection.definitions.get(schema_title)
            self.definitions=items

            for item in items:
                text = '{}'.format(item.get('name'))
                if not self.definition_filter:
                    text = '{} - {}'.format(
                        schema.get('title'),
                        item.get('name')
                    )
                self.definition_combobox.addItem(text, item)

        if len(self.definitions) == 1:
            self.definition_combobox.setCurrentIndex(1)
            self.definition_combobox.hide()
        else:
            self.definition_combobox.show()

    def _on_select_definition(self, index):
        self.definition = self.definition_combobox.itemData(index)

        if not self.definition:
            self.logger.debug('No data for selected definition')
            self.definition_changed.emit(None, None)
            return

        for schema in self.schemas:
            if (
                    self.definition.get('type').lower() ==
                    schema.get('title').lower()
            ):
                self.schema = schema
                break

        self.definition_changed.emit(self.schema, self.definition)

    def add_hosts(self, host_connections):
        for host_connection in host_connections:
            self.host_combobox.addItem(host_connection.name, host_connection)
            self.host_connections.append(host_connection)
        if len(host_connections) == 1 and host_connections[0].context_id != None:
            self.host_combobox.setCurrentIndex(1)

    def set_definition_filter(self, filter):
        self.definition_filter = filter

    def get_current_definition_index(self):
        return self.definition_combobox.currentIndex()

    def set_current_definition_index(self, index):
        self.definition_combobox.setCurrentIndex(index)
        self._on_select_definition(index)


class DefinitionSelectorButtons(DefinitionSelector):
    '''DefinitionSelector Base Class'''
    definition_changed = QtCore.Signal(object, object)
    host_changed = QtCore.Signal(object)
    max_column = 3

    def __init__(self, parent=None):
        '''Initialize DefinitionSelector widget'''
        super(DefinitionSelectorButtons, self).__init__(parent=parent)

    def build(self):
        self.host_combobox = QtWidgets.QComboBox()

        self.definitions_widget = QtWidgets.QWidget()

        self.definitions_widget.setLayout(QtWidgets.QVBoxLayout())
        self.definitions_widget.layout().setContentsMargins(0, 0, 0, 0)

        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(QtWidgets.QHBoxLayout())
        header_widget.layout().setContentsMargins(0, 0, 0, 0)
        header_widget.layout().setSpacing(0)

        self.label = QtWidgets.QLabel("Choose what to publish")
        header_widget.layout().addWidget(self.label)
        header_widget.layout().addStretch()

        self.start_over_button = QtWidgets.QPushButton("START OVER")
        self.start_over_button.setObjectName('borderless')
        self.start_over_button.clicked.connect(self._start_over)
        header_widget.layout().addWidget(self.start_over_button)

        self.definitions_widget.layout().addWidget(header_widget)

        self.button_group = QtWidgets.QButtonGroup(self)
        self.definition_buttons_widget = QtWidgets.QWidget()
        self.definition_buttons_widget.setLayout(QtWidgets.QHBoxLayout())
        self.definition_buttons_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.definition_buttons_widget.layout().setSpacing(0)

        self.definitions_widget.layout().addWidget(self.definition_buttons_widget)

        self.layout().addWidget(self.host_combobox)
        self.layout().addWidget(self.definitions_widget)

        self.host_combobox.addItem('- Select host -')

    def post_build(self):
        '''Connect the widget signals'''
        self.host_combobox.currentIndexChanged.connect(self._on_change_host)

    def _on_change_host(self, index):
        '''triggered when chaging host selection to *index*'''
        self.clear_definitions()
        self.host_connection = self.host_combobox.itemData(index)
        self.host_changed.emit(self.host_connection)

        if not self.host_connection:
            self.logger.debug('No data for selected host')
            return

        self.schemas = [
            schema for schema in self.host_connection.definitions['schema']
            if schema.get('title').lower() != 'package'
        ]

        self._populate_definitions()

    def clear_definitions(self):
        buttons = self.button_group.buttons()
        for button in buttons:
            self.button_group.removeButton(button)
            button.deleteLater()

    def _populate_definitions(self):

        self.definitions = []
        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self.definition_filter:
                if schema_title != self.definition_filter:
                    continue
            items = self.host_connection.definitions.get(schema_title)
            self.definitions = items

            index = 0
            for item in items:
                text = '{}'.format(' '.join(item.get('name').split(' ')[:-1]))  # Remove ' Publisher'
                if not self.definition_filter:
                    text = '{} - {}'.format(
                        schema.get('title'),
                        item.get('name')
                    )
                definition_button = DefinitionItem(text.upper(), item)
                self.button_group.addButton(definition_button)
                self.definition_buttons_widget.layout().addWidget(definition_button)
                definition_button.clicked.connect(partial(self._on_select_definition, definition_button))
                if index == 0:
                    definition_button.click()
                index+=1

        self.definition_buttons_widget.layout().addWidget(QtWidgets.QLabel(), 100)

        # if len(self.definitions) == 1:
        #     self.definitions_widget.hide()
        #     self.definitions_text.setText(self.definition.get('name'))
        #     self.layout().addWidget(self.definitions_text)
        # else:
        #   self.definitions_text.setText("Choose what to publish:")
        #   self.definitions_widget.layout().insertWidget(0, self.definitions_text)
        self.definitions_widget.show()

    def _on_select_definition(self, definition_item):
        definition_item.setEnabled(False)
        for button in self.button_group.buttons():
            if not button is definition_item:
                button.setEnabled(True)
        self.definition = definition_item.definition

        if not self.definition:
            self.logger.debug('No data for selected definition')
            self.definition_changed.emit(None, None)
            return

        for schema in self.schemas:
            if (
                    self.definition.get('type').lower() ==
                    schema.get('title').lower()
            ):
                self.schema = schema
                break

        self.definition_changed.emit(self.schema, self.definition)

    def get_current_definition_index(self):
        return self.button_group.checkedId()

    def set_current_definition_index(self, index):
        button = self.button_group.button(index)
        self._on_select_definition(button)

    def _start_over(self):
        self._on_select_definition(self.button_group.checkedButton())