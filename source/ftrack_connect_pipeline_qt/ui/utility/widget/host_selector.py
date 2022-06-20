import logging

from Qt import QtWidgets, QtCore


class HostSelector(QtWidgets.QWidget):
    '''Host selector widget. Hides the widget input if only one host (default usage scenario within DCCs)'''

    hostChanged = QtCore.Signal(object)  # The host has been changed by user

    @property
    def host_connection(self):
        '''Return the current selected host connection, 1-based (0 is no host selected)'''
        return self.host_combobox.itemData(self.host_combobox.currentIndex())

    @host_connection.setter
    def host_connection(self, value):
        '''Set the current selected host connection to *value*'''
        for index in range(self.host_combobox.count()):
            if self.host_combobox.itemData(index) == value:
                self.host_combobox.setCurrentIndex(index)
                return
        self.host_combobox.setCurrentIndex(0)

    def __init__(self, client, parent=None):
        '''
        Initialize HostSelector widget

        :param client: :class:`~ftrack_connect_pipeline.client.Client` instance
        :param parent: The parent dialog or frame
        '''
        super(HostSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.pre_build()
        self.build()
        self.post_build()

        if client.host_connections:
            self.add_hosts(client.host_connections)
            if client.host_connection:
                self.host_connection = client.host_connection

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
        '''Add the host(connections) to combobox. If only one, select it (default behaviour)'''
        for host_connection in host_connections:
            self.host_combobox.addItem(
                '{}({})'.format(host_connection.name, host_connection.id),
                host_connection,
            )
        if self.host_combobox.count() == 2:
            self.host_combobox.setCurrentIndex(1)
            self.setVisible(False)
        else:
            self.setVisible(True)

    def _on_host_selected(self, index):
        '''Triggered when changing host selection to *index*'''
        host_connection = self.host_combobox.itemData(index)

        if not host_connection:
            self.logger.warning('No data for selected host')

        self.hostChanged.emit(host_connection)
