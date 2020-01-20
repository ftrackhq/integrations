import logging
from Qt import QtWidgets, QtCore


class HostSelector(QtWidgets.QWidget):
    definition_changed = QtCore.Signal(object, object, object)
    host_connection = None
    schemas = None

    @property
    def selected_host_connection(self):
        return self._get_selected_host_connection()

    def __init__(self, parent=None):
        super(HostSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        main_layout = QtWidgets.QVBoxLayout()

        self.setLayout(main_layout)

        self.host_combobox = QtWidgets.QComboBox()
        self.definition_combobox = QtWidgets.QComboBox()

        self.layout().addWidget(self.host_combobox)
        self.layout().addWidget(self.definition_combobox)

        self.host_combobox.addItem('- Select host -')

        self.connect_signals()

    def connect_signals(self):
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
            schema for schema in self.host_connection.definitions['schemas']
            if schema.get('title') == "Publisher" or
               schema.get('title') == "Loader"
        ]
        self._populate_definitions()

    def _on_select_definition(self, index):
        self.definition = self.definition_combobox.itemData(index)
        if not self.definition:
            self.logger.warning("No data for selected definition")
            return
        for schema in self.schemas:
            if self.definition.get('type') == "publisher":
                if schema.get('title') == "Publisher":
                    self.schema = schema
                    break
            elif self.definition.get('type') == "loader":
                if schema.get('title') == "Loader":
                    self.schema = schema
                    break

        self.definition_changed.emit(self.host_connection, self.schema,
                                     self.definition)

    def _get_selected_host_connection(self):
        return self.host_combobox.itemData(
            self.self.host_combobox.currentIndex()
        )

    def _populate_definitions(self):
        self.definition_combobox.addItem('- Select Definition -')
        for schema in self.schemas:
            if schema.get('title') == "Publisher":
                self._populatePublishers(
                    self.host_connection.definitions['publishers']
                )
            if schema.get('title') == "Loader":
                self._populateLoaders(
                    self.host_connection.definitions['loaders']
                )

    def _populatePublishers(self, publishers):
        for publisher in publishers:
            name = "Publisher : {}".format(publisher['name'])
            self.definition_combobox.addItem(name, publisher)

    def _populateLoaders(self, loaders):
        for loader in loaders:
            name = "Loader : {}".format(loader['name'])
            self.definition_combobox.addItem(name, loader)

    def addHost(self, id, host_connection):
        self.host_combobox.addItem(id, host_connection)

