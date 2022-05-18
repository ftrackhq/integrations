import logging

from Qt import QtWidgets, QtCore


class HostSelector(QtWidgets.QWidget):
    '''Host selector Class. Hides the widget input
    if only one host (default usage scenario within DCCs)'''

    hostChanged = QtCore.Signal(object)

    @property
    def host_connection(self):
        return self.host_combobox.itemData(self.host_combobox.currentIndex())

    def __init__(self, parent=None):
        '''Initialize DefinitionSelector widget'''
        super(HostSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 5, 0, 5)
        self.layout().setSpacing(10)

    def build(self):
        l_host = QtWidgets.QLabel('Select host')
        self.layout().addWidget(l_host)

        self.host_combobox = QtWidgets.QComboBox()
        self.layout().addWidget(self.host_combobox, 10)

        self.host_combobox.addItem('', None)

    def post_build(self):
        '''Connect the widget signals'''
        self.host_combobox.currentIndexChanged.connect(self._on_host_selected)
        self.setVisible(False)

    def add_hosts(self, host_connections):
        for host_connection in host_connections:
            self.host_combobox.addItem(host_connection.name, host_connection)
        if self.host_combobox.count() == 2:
            self.host_combobox.setCurrentIndex(1)
            self.setVisible(False)
        else:
            self.setVisible(True)

    def _on_host_selected(self, index):
        '''triggered when chaging host selection to *index*'''
        host_connection = self.host_combobox.itemData(index)

        if not host_connection:
            self.logger.warning('No data for selected host')

        self.hostChanged.emit(host_connection)
