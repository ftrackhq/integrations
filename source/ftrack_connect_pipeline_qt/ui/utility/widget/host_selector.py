import logging
from Qt import QtWidgets, QtCore


class HostSelector(QtWidgets.QWidget):
    '''HostSelector Base Class'''
    definition_changed = QtCore.Signal(object, object, object)
    host_connection = None
    schemas = None
    definition_filter = None

    @property
    def selected_host_connection(self):
        return self.host_combobox.itemData(
            self.host_combobox.currentIndex()
        )

    def __init__(self, parent=None):
        '''Initialize HostSelector widget'''
        super(HostSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.hosts = []
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

    def _on_change_host(self, index):
        '''triggered when chaging host selection to *index*'''
        self.definition_combobox.clear()
        self.host_connection = self.host_combobox.itemData(index)

        if not self.host_connection:
            self.logger.warning('No data for selected host')
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
                self.definition_combobox.addItem(
                    '{} - {}'.format(
                        schema.get('title'),
                        item.get('name')
                    ), item)

    def _on_select_definition(self, index):
        self.definition = self.definition_combobox.itemData(index)

        if not self.definition:
            self.logger.warning('No data for selected definition')
            return

        for schema in self.schemas:
            if (
                    self.definition.get('type').lower() ==
                    schema.get('title').lower()
            ):
                self.schema = schema
                break

        self.definition_changed.emit(
            self.host_connection,
            self.schema,
            self.definition)

    def add_hosts(self, hosts):
        for host in hosts:
            self.host_combobox.addItem(host.id, host)

    def set_definition_filter(self, filter):
        self.definition_filter = filter

