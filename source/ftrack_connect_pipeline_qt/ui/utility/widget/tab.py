# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtWidgets, QtCore, QtGui


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, horizontal=True, parent=None):
        super(TabWidget, self).__init__(parent=parent)
