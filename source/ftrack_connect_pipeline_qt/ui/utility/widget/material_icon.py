# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack
import qtawesome as qta

from Qt import QtWidgets, QtCore, QtGui

class MaterialIconWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, name=None):
        super(MaterialIconWidget, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(1)
        if name:
            self.set_icon(name)

    def set_icon(self, name, color='gray'):
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        label = QtWidgets.QLabel()
        icon = qta.icon('mdi6.{}'.format(name), color=color)
        label.setPixmap(icon.pixmap(QtCore.QSize(16, 16)))
        self.layout().addWidget(label)