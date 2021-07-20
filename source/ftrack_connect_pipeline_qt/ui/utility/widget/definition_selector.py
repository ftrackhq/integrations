import logging
from Qt import QtWidgets, QtCore


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

        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self.definition_filter:
                if schema_title != self.definition_filter:
                    continue
            items = self.host_connection.definitions.get(schema_title)

            for item in items:
                text = '{}'.format(item.get('name'))
                if not self.definition_filter:
                    text = '{} - {}'.format(
                        schema.get('title'),
                        item.get('name')
                    )
                self.definition_combobox.addItem(text, item)

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

