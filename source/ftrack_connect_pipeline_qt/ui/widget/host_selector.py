import logging
from Qt import QtWidgets, QtCore, QtGui


class HostComboBox(QtWidgets.QComboBox):
    hostid_changed = QtCore.Signal(object)

    @property
    def selected_host_connection(self):
        return self._get_selected_host_connection()

    def __init__(self, parent=None):
        super(HostComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.addItem('- Select host -')
        self.connect_signals()

    def connect_signals(self):
        self.currentIndexChanged.connect(self.on_change_host)

    def on_change_host(self, index):
        '''triggered when chaging host selection to *index*'''

        host_connection = self.itemData(index)
        if not host_connection:
            self.logger.warning("No data for selected host")
            return
        self.hostid_changed.emit(host_connection)

    def _get_selected_host_connection(self):
        return self.itemData(self.currentIndex())
