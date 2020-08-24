# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial
from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_const

from ftrack_connect_pipeline_qt.ui.asset_manager.model.asset_manager import (
    AssetManagerModel, FilterProxyModel
)
from ftrack_connect_pipeline_qt.ui.asset_manager.delegate.asset_manager import (
    VersionDelegate
)


class AssetManagerWidget(QtWidgets.QWidget):
    widget_status_updated = QtCore.Signal(object)
    change_asset_version = QtCore.Signal(object, object)

    @property
    def event_manager(self):
        return self._event_manager

    @property
    def session(self):
        return self.event_manager.session

    @property
    def engine_type(self):
        '''Returns ftrack object from the DCC app'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        self._engine_type = value

    def __init__(self, event_manager, parent=None):
        super(AssetManagerWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._engine_type = None

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

        self.asset_table_view = AssetManagerTableView(
            self.event_manager, parent=self
        )
        self.layout().addWidget(self.asset_table_view)

    def post_build(self):
        self.filter_field.textChanged.connect(self.on_search)
        self.asset_table_view.version_cb_delegate.change_version.connect(
            self.on_asset_change_version
        )
    def on_asset_change_version(self, index, value):
        asset_info = self.asset_table_view.asset_model.ftrack_asset_list[
            index.row()
        ]
        self.change_asset_version.emit(asset_info, value)

    def set_asset_list(self, ftrack_asset_list):
        self.ftrack_asset_list = ftrack_asset_list
        self.asset_table_view.set_asset_list(self.ftrack_asset_list)

    def on_search(self):
        '''Search in the current model.'''
        value = self.filter_field.text()
        self.asset_table_view.model().setFilterWildcard(value)

    def set_host_connection(self, host_connection):
        self.host_connection = host_connection
        self._listen_widget_updates()
        self.asset_table_view.set_host_connection(self.host_connection)

    def set_context_actions(self, actions):
        self.asset_table_view.engine_type = self.engine_type
        self.asset_table_view.create_actions(actions)

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        pass

    def _listen_widget_updates(self):
        '''Subscribe to the PIPELINE_CLIENT_NOTIFICATION topic to call the
        _update_widget function when the host returns and answer through the
        same topic'''

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.hostid={}'.format(
                core_const.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._update_widget
        )


class AssetManagerTableView(QtWidgets.QTableView):
    '''Model representing AssetManager.'''

    @property
    def event_manager(self):
        return self._event_manager

    @property
    def engine_type(self):
        '''Returns ftrack object from the DCC app'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        self._engine_type = value

    @property
    def session(self):
        return self.event_manager.session

    def __init__(self, event_manager, parent=None):
        '''Initialise browser with *root* entity.

        Use an empty *root* to start with list of projects.

        *parent* is the optional owner of this UI element.

        '''
        super(AssetManagerTableView, self).__init__(parent=parent)

        self.ftrack_asset_list = []
        self.action_widgets = {}
        self._engine_type = None

        self._event_manager = event_manager

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
            self.asset_model.get_version_column_index(), self.version_cb_delegate
        )

    def post_build(self):
        '''Perform post-construction operations.'''
        pass
        # self.version_cb_delegate.change_version.connect(
        #     self.on_asset_change_version
        # )
    #
    # def on_asset_change_version(self, index, value):
    #     ftrack_asset_info = self.asset_model.ftrack_asset_list[index.row()]
    #     self.change_asset_version.emit(ftrack_asset_info, value)
    #     # ftrack_asset_info.change_version(value, self.host_connection)
    #
    #     # self.asset_model.setData(
    #     #     index, value, QtCore.Qt.EditRole
    #     # )

    def set_asset_list(self, ftrack_asset_list):
        self.ftrack_asset_list = ftrack_asset_list
        self.asset_model.set_asset_list(self.ftrack_asset_list)

    def create_actions(self, actions):
        self.action_widgets = {}
        for action_type, actions in actions.items():
            if action_type not in self.action_widgets.keys():
                self.action_widgets[action_type] = []
            for action in actions:
                action_widget = QtWidgets.QAction(action['name'], self)
                action_widget.setData(action)
                self.action_widgets[action_type].append(action_widget)

    def contextMenuEvent(self, event):
        self.menu = QtWidgets.QMenu(self)
        self.action_type_menu = {}
        for action_type, action_widgets in self.action_widgets.items():
            if action_type not in self.action_type_menu.keys():
                type_menu = QtWidgets.QMenu(action_type, self)
                self.menu.addMenu(type_menu)
                self.action_type_menu[action_type] = type_menu
            for action_widget in action_widgets:
                self.action_type_menu[action_type].addAction(action_widget)
        self.menu.triggered.connect(self.menu_triggered)

        # add other required actions
        self.menu.exec_(QtGui.QCursor.pos())

    def menu_triggered(self, action):
        plugin = action.data()
        ui_callback = plugin['ui_callback']
        if hasattr(self, ui_callback):
            callback_fn = getattr(self, ui_callback)
            callback_fn(plugin)

    def ctx_update(self, plugin):
        index_list = self.selectionModel().selectedRows()
        for index in index_list:
            data = self.model().data(index, self.model().DATA_ROLE)

            plugin['plugin_data'] = data
            self.host_connection.run(
                plugin, self.engine_type, partial(self._update_callback, index=index)
            )

    def _update_callback(self, event, index):
        data = event['data']
        if len(data) <= 0:
            self.logger.warning("Id not found to update version")
            return
        new_id = data[0]

        self.asset_model.setData(
            index, new_id, QtCore.Qt.EditRole
        )

    def ctx_select(self, plugin):
        index_list = self.selectionModel().selectedRows()
        i=0
        for index in index_list:
            data = self.model().data(index, self.model().DATA_ROLE)
            # Clear the selection before select the first asset in the loop,
            # then append the others to the selection.
            if i==0:
                plugin['options']['clear_selection'] = True
            else:
                plugin['options']['clear_selection'] = False
            plugin['plugin_data'] = data
            self.host_connection.run(plugin, self.engine_type)
            i+=1

    def ctx_remove(self, plugin):
        index_list=[]
        for model_index in self.selectionModel().selectedRows():
            index = QtCore.QPersistentModelIndex(model_index)
            index_list.append(index)

        for index in index_list:
            data = self.model().data(index, self.model().DATA_ROLE)
            plugin['plugin_data'] = data
            self.host_connection.run(
                plugin, self.engine_type, partial(self._remove_callback, index=index)
            )

    def _remove_callback(self, event, index):
        self.model().removeRow(index.row())

    def set_host_connection(self, host_connection):
        self.host_connection = host_connection
        self.asset_model.set_host_connection(self.host_connection)