try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui


class WidgetList(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(WidgetList, self).__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.tablewidget = QtWidgets.QListWidget()
        self.tablewidget.itemChanged.connect(self._set_state)
        layout.addWidget(self.tablewidget)

    def _add_plugins(self, plugins):
        for plugin_name, plugin_object in plugins.items():
            new_item = QtWidgets.QListWidgetItem(plugin_name)
            new_item.setData(QtCore.Qt.ItemDataRole.UserRole, plugin_object)
            new_item.setFlags(
                new_item.flags()
                | QtCore.Qt.ItemFlag.ItemIsSelectable
                | QtCore.Qt.ItemFlag.ItemIsUserCheckable
            )
            new_item.setCheckState(QtCore.Qt.CheckState.Checked)
            self.tablewidget.addItem(new_item)

    def _set_state(self, item):
        connect_widget = item.data(QtCore.Qt.ItemDataRole.UserRole)
        # hide / show tab containing the plugin.
        connect_widget.parent().parent().setVisible(item.checkState())
