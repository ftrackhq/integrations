# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.ui.asset_manager.model.asset_manager import (
    AssetManagerModel, FilterProxyModel
)
from ftrack_connect_pipeline_qt.ui.asset_manager.delegate.asset_manager import (
    VersionDelegate
)


class AssetManagerWidget(QtWidgets.QWidget):
    widget_status_updated = QtCore.Signal(object)

    def __init__(self, event_manager, parent=None):
        super(AssetManagerWidget, self).__init__(parent=parent)

        self.session = event_manager.session
        self._event_manager = event_manager

        self.ftrack_asset_list = []

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)

    def build(self):
        filter_layout = QtWidgets.QHBoxLayout()
        filter_label = QtWidgets.QLabel('Filter')
        self.filter_field = QtWidgets.QLineEdit()
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_field)
        self.layout().addLayout(filter_layout)

        self.asset_table_view = AssetManagerTableView(self.session, parent=self)
        self.layout().addWidget(self.asset_table_view)

    def post_build(self):
        self.filter_field.textChanged.connect(self.on_search)

    def add_asset_list(self, ftrack_asset_list):
        self.ftrack_asset_list = ftrack_asset_list
        self.asset_table_view.add_asset_list(self.ftrack_asset_list)

    def on_search(self):
        '''Search in the current model.'''
        value = self.filter_field.text()
        self.asset_table_view.model().setFilterWildcard(value)

    def set_host_connection(self, host_connection):
        self.host_connection = host_connection
        self._listen_widget_updates()
        self.asset_table_view.set_host_connection(self.host_connection)

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        pass
        # result = event['data']['pipeline']['result']
        # widget_ref = event['data']['pipeline']['widget_ref']
        # status = event['data']['pipeline']['status']
        # message = event['data']['pipeline']['message']
        # host_id = event['data']['pipeline']['hostid']
        #
        # widget = self.widgets.get(widget_ref)
        # if not widget:
        #     self.logger.debug(
        #         'Widget ref :{} not found for hostid {} ! '.format(
        #             widget_ref, host_id
        #         )
        #     )
        #     return
        #
        # if status:
        #     self.logger.debug(
        #         'updating widget: {} with {}, {}'.format(
        #             widget, status, message
        #         )
        #     )
        #     widget.set_status(status, message)

    def _listen_widget_updates(self):
        '''Subscribe to the PIPELINE_CLIENT_NOTIFICATION topic to call the
        _update_widget function when the host returns and answer through the
        same topic'''

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.hostid={}'.format(
                core_constants.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._update_widget
        )


class AssetManagerTableView(QtWidgets.QTableView):
    '''Model representing AssetManager.'''

    def __init__(self, session, parent=None):
        '''Initialise browser with *root* entity.

        Use an empty *root* to start with list of projects.

        *parent* is the optional owner of this UI element.

        '''
        super(AssetManagerTableView, self).__init__(parent=parent)

        self.ftrack_asset_list = []

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

        self.asset_model = AssetManagerModel(parent=self)
        self.proxy_model = FilterProxyModel(parent=self)
        self.proxy_model.setSourceModel(self.asset_model)

        self.setModel(self.proxy_model)
        self.version_cb_delegate = VersionDelegate(self)

        self.setItemDelegateForColumn(
            self.proxy_model.get_version_column_idx(), self.version_cb_delegate
        )

    def post_build(self):
        '''Perform post-construction operations.'''
        pass

    def add_asset_list(self, ftrack_asset_list):
        self.ftrack_asset_list = ftrack_asset_list
        self.asset_model.add_asset_list(self.ftrack_asset_list)

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
            latest_versions = data.asset_versions[-1]
            self.asset_model.setData(
                row, latest_versions['id'], QtCore.Qt.EditRole
            )

    def set_host_connection(self, host_connection):
        self.host_connection = host_connection
        self.asset_model.set_host_connection(self.host_connection)