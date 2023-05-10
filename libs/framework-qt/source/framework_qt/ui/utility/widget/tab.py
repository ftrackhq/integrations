# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets, QtCore, QtGui


class TabWidget(QtWidgets.QTabWidget):
    '''Tab widget wrapper'''

    def __init__(self, horizontal=True, parent=None):
        super(TabWidget, self).__init__(parent=parent)
