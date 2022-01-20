# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from functools import partial

from Qt import QtWidgets, QtCore, QtCompat, QtGui


class AssetListWidget(QtWidgets.QFrame):
    '''
    Display a list if assets, with a title.
    '''

    header_clicked = QtCore.Signal()

    def __init__(self, title, parent=None):
        super(AssetListWidget, self).__init__(parent=parent)

        self._title = title

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout(self))

    def build(self):
        '''Build widgets and parent them.'''

        self._header = QtWidgets.QWidget()
        self._header.setLayout(QtWidgets.QHBoxLayout())
        title_label = QtWidgets.QLabel(self._title or '')
        self._header.layout().addWidget(title_label)
        self.layout().addWidget(self._header)

        self._list = AssetList()
        # The list height will be dynamically set depending on row height
        self.layout().addWidget(self._list)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        pass


class AssetList(QtWidgets.QListWidget):
    '''Widget presenting list assets'''

    def __init__(self, session, parent=None):
        super(AssetList, self).__init__(parent=parent)
