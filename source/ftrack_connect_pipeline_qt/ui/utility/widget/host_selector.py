import logging
from Qt import QtWidgets, QtCore


class HostSelector(QtWidgets.QWidget):
    '''DefinitionSelector Base Class'''
    host_changed = QtCore.Signal(object)
    host_connection = None

    @property
    def selected_host_connection(self):
        return self.host_combobox.itemData(
            self.host_combobox.currentIndex()
        )

    def __init__(self, parent=None):
        '''Initialize DefinitionSelector widget'''
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

        self.layout().addWidget(self.host_combobox)

        self.host_combobox.addItem('- Select host -')

    def post_build(self):
        '''Connect the widget signals'''
        self.host_combobox.currentIndexChanged.connect(self._on_change_host)

    def _on_change_host(self, index):
        '''triggered when chaging host selection to *index*'''
        self.host_connection = self.host_combobox.itemData(index)

        if not self.host_connection:
            self.logger.warning('No data for selected host')
            return

        self.host_changed.emit(self.host_connection)

    def add_hosts(self, hosts):
        for host in hosts:
            self.host_combobox.addItem(host.id, host)


