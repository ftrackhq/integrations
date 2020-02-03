import logging
from Qt import QtWidgets, QtCore


class HostSelector(QtWidgets.QWidget):
    '''HostSelector Base Class'''
    definition_changed = QtCore.Signal(object, object, object)
    host_connection = None
    schemas = None

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
            self.logger.warning("No data for selected host")
            return

        self.schemas = [
            schema for schema in self.host_connection.definitions['schema']
            if schema.get('title') != "Package"
        ]

        self._populate_definitions()

    def _on_select_definition(self, index):
        self.definition = self.definition_combobox.itemData(index)
        if not self.definition:
            self.logger.warning("No data for selected definition")
            return

        for schema in self.schemas:
            if (
                    self.definition.get('type').lower() ==
                    schema.get('title').lower()
            ):
                print 'schema', schema['title']
                self.schema = schema
                break

        self.definition_changed.emit(
            self.host_connection,
            self.schema,
            self.definition)

    def _populate_definitions(self):
        self.definition_combobox.addItem('- Select Definition -')
        for schema in self.schemas:
            print schema.get('title').lower()
            item = self.host_connection.definitions.get(
                schema.get('title').lower()
            )

            print 'item',  item

            if not item:
                return
            self.definition_combobox.addItem(schema.get('title'), item)

    def addHost(self, host):
        self.host_combobox.addItem(host.id, host)

