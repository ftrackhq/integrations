# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline_qt.ui.utility.model.asset_manager import AssetManagerModel, FilterProxyModel
from ftrack_connect_pipeline_qt.ui.utility.delegate.asset_manager import (
    VersionDelegate
)


class AssetManagerWidget(QtWidgets.QWidget):

    def __init__(self, ftrack_asset_list, session, parent=None):
        super(AssetManagerWidget, self).__init__(parent=parent)
        self.session = session
        self.ftrack_asset_list = ftrack_asset_list

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)

    def build(self):
        filter_layout = QtWidgets.QHBoxLayout()
        filter_label = QtWidgets.QLabel('Filter:')
        self.filter_field = QtWidgets.QLineEdit()
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_field)
        self.layout().addLayout(filter_layout)

        self.asset_list = AssetManagerTableView(self.ftrack_asset_list, self.session, parent=self)
        self.layout().addWidget(self.asset_list)

    def post_build(self):
        self.filter_field.textChanged.connect(self.on_search)

    def on_search(self):
        '''Search in the current model.'''
        value = self.filter_field.text()
        self.asset_list.model().setFilterWildcard(value)


class AssetManagerTableView(QtWidgets.QTableView):
    '''Model representing AssetManager.'''

    def __init__(self, ftrack_asset_list, session, parent=None):
        '''Initialise browser with *root* entity.

        Use an empty *root* to start with list of projects.

        *parent* is the optional owner of this UI element.

        '''
        super(AssetManagerTableView, self).__init__(parent=parent)

        self.ftrack_asset_list = ftrack_asset_list

        self._session = session

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setAlternatingRowColors(True)
        self.verticalHeader().hide()

        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )

        QtCompat.setSectionResizeMode(
            self.verticalHeader(),
            QtWidgets.QHeaderView.ResizeToContents
        )

        self.horizontalHeader().setStretchLastSection(True)

    def build(self):

        self.asset_model = AssetManagerModel(
            ftrack_asset_list=self.ftrack_asset_list, parent=self
        )
        self.proxy_model = FilterProxyModel(parent=self)
        self.proxy_model.setSourceModel(self.asset_model)

        self.setModel(self.proxy_model)
        self.version_cb_delegate = VersionDelegate(self)

        self.setItemDelegateForColumn(
            self.proxy_model.get_version_column_idx(), self.version_cb_delegate
        )

    def post_build(self):
        '''Perform post-construction operations.'''

    def contextMenuEvent(self, event):
        self.menu = QtWidgets.QMenu(self)
        self.udpate_action = QtWidgets.QAction('Update to latest', self)
        self.udpate_action.triggered.connect(lambda: self.ctx_update_to_latest(event))
        self.menu.addAction(self.udpate_action)
        # add other required actions
        self.menu.exec_(QtGui.QCursor.pos())

    def ctx_update_to_latest(self, event):
        rows = self.selectionModel().selectedRows()
        for row in rows:
            data = self.model().data(row, self.model().DATA_ROLE)
            print data.asset_info

