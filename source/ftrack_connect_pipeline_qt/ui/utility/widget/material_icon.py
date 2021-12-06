# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack
import qtawesome as qta

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt import constants

class MaterialIconWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, name=None):
        super(MaterialIconWidget, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(1)
        if name:
            self.set_icon(name)

    def set_icon(self, name, color='gray', size=16):
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        label = QtWidgets.QLabel()
        icon = qta.icon('mdi6.{}'.format(name), color=color)
        label.setPixmap(icon.pixmap(QtCore.QSize(size, size)))
        self.layout().addWidget(label)

    def set_status(self, status, size=16):
        icon_name = ''
        color = '303030'
        if status in [constants.UNKNOWN_STATUS, constants.DEFAULT_STATUS]:
            icon_name = 'help'
            color = '303030'
        elif status in [constants.RUNNING_STATUS]:
            icon_name = 'loading'
            color = '87E1EB'
        elif status in [constants.SUCCESS_STATUS]:
            icon_name = 'check-circle-outline'
            color = '79DFB6'
        elif status in [constants.ERROR_STATUS, constants.EXCEPTION_STATUS]:
            icon_name = 'alert-circle-outline'
            color = 'FF7A73'
        self.set_icon(icon_name, color='#{}'.format(color), size=size)