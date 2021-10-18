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
    ''' Main widget of the asset manager '''
    widget_status_updated = QtCore.Signal(object)
    change_asset_version = QtCore.Signal(object, object)
    select_assets = QtCore.Signal(object)
    remove_assets = QtCore.Signal(object)
    update_assets = QtCore.Signal(object, object)
    load_assets = QtCore.Signal(object, object)
    unload_assets = QtCore.Signal(object, object)

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    @property
    def engine_type(self):
        '''Returns engine_type'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        '''Sets the engine_type with the given *value*'''
        self._engine_type = value

    def __init__(self, event_manager, parent=None):
        '''Initialise AssetManagerWidget with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.
        '''
        super(AssetManagerWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._engine_type = None

        self.asset_entities_list = []

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)

    def build(self):
        '''Build widgets and parent them.'''
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
        '''Post Build ui method for events connections.'''
        self.filter_field.textChanged.connect(self.on_search)
        self.asset_table_view.version_cb_delegate.change_version.connect(
            self.on_asset_change_version
        )
        self.asset_table_view.select_assets.connect(
            self.on_select_assets
        )
        self.asset_table_view.remove_assets.connect(
            self.on_remove_assets
        )
        self.asset_table_view.update_assets.connect(
            self.on_update_assets
        )

        self.asset_table_view.load_assets.connect(
            self.on_load_assets
        )
        self.asset_table_view.unload_assets.connect(
            self.on_unload_assets
        )

    def on_asset_change_version(self, index, value):
        '''
        Triggered when a version of the asset has changed on the
        :obj:`version_cb_delegate`
        '''
        _asset_info = self.asset_table_view.asset_model.asset_entities_list[
            index.row()
        ]
        # Copy to avoid update automatically
        asset_info = _asset_info.copy()
        self.change_asset_version.emit(asset_info, value)

    def on_select_assets(self, assets):
        '''
        Triggered when select action is clicked on the asset_table_view.
        '''
        self.select_assets.emit(assets)

    def on_remove_assets(self, assets):
        '''
        Triggered when remove action is clicked on the asset_table_view.
        '''
        self.remove_assets.emit(assets)

    def on_update_assets(self, assets, plugin):
        '''
        Triggered when update action is clicked on the asset_table_view.
        '''
        self.update_assets.emit(assets, plugin)

    def on_load_assets(self, assets):
        '''
        Triggered when load action is clicked on the asset_table_view.
        '''
        self.load_assets.emit(assets)

    def on_unload_assets(self, assets):
        '''
        Triggered when unload action is clicked on the asset_table_view.
        '''
        self.unload_assets.emit(assets)

    def set_asset_list(self, asset_entities_list):
        '''
        Sets the :obj:`asset_entities_list` with the given *asset_entities_list*
        '''
        self.asset_entities_list = asset_entities_list
        self.asset_table_view.set_asset_list(self.asset_entities_list)

    def on_search(self):
        '''Search in the current model.'''
        value = self.filter_field.text()
        self.asset_table_view.model().setFilterWildcard(value)

    def set_host_connection(self, host_connection):
        '''Sets :obj:`host_connection` with the given *host_connection*.'''
        self.host_connection = host_connection
        self._listen_widget_updates()
        self.asset_table_view.set_host_connection(self.host_connection)

    def set_context_actions(self, actions):
        '''Set the :obj:`engine_type` into the asset_table_view and calls the
        create_action function of the same class with the given *actions*'''
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
            'topic={} and data.pipeline.host_id={}'.format(
                core_const.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._update_widget
        )


class AssetManagerTableView(QtWidgets.QTableView):
    '''Table view representing AssetManager.'''
    select_assets = QtCore.Signal(object)
    remove_assets = QtCore.Signal(object)
    update_assets = QtCore.Signal(object, object)
    load_assets = QtCore.Signal(object)
    unload_assets = QtCore.Signal(object)

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def engine_type(self):
        '''Returns engine_type'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        '''Sets the engine_type with the given *value*'''
        self._engine_type = value

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def __init__(self, event_manager, parent=None):
        '''Initialise AssetManagerTableView with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.
        '''
        super(AssetManagerTableView, self).__init__(parent=parent)

        self.asset_entities_list = []
        self.action_widgets = {}
        self._engine_type = None

        self._event_manager = event_manager

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
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
        '''Build widgets and parent them.'''
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

    def set_asset_list(self, asset_entities_list):
        '''
        Sets the :obj:`asset_entities_list` with the given *asset_entities_list*
        '''
        self.asset_entities_list = asset_entities_list
        self.asset_model.set_asset_list(self.asset_entities_list)

    def create_actions(self, actions):
        '''
        Creates all the actions for the context menu.
        '''
        self.action_widgets = {}
        #TODO: decide if to add the actions here or in the definition like the update one
        default_actions = {
            'select': [{
                'ui_callback': 'ctx_select',
                'name': 'select_asset'
            }],
            'remove': [{
                'ui_callback': 'ctx_remove',
                'name': 'remove_asset'
            }]
            # 'load': [{
            #     'ui_callback': 'ctx_load',
            #     'name': 'load_asset'
            # }],
            # 'unload': [{
            #     'ui_callback': 'ctx_unload',
            #     'name': 'unload_asset'
            # }]
        }
        for def_action_type, def_action in list(default_actions.items()):
            if def_action_type in list(actions.keys()):
                actions[def_action_type].extend(def_action)

        for action_type, actions in list(actions.items()):
            if action_type not in list(self.action_widgets.keys()):
                self.action_widgets[action_type] = []
            for action in actions:
                action_widget = QtWidgets.QAction(action['name'], self)
                action_widget.setData(action)
                self.action_widgets[action_type].append(action_widget)

    def contextMenuEvent(self, event):
        '''
        Executes the context menu
        '''
        self.menu = QtWidgets.QMenu(self)
        self.action_type_menu = {}
        for action_type, action_widgets in list(self.action_widgets.items()):
            if action_type not in list(self.action_type_menu.keys()):
                type_menu = QtWidgets.QMenu(action_type, self)
                self.menu.addMenu(type_menu)
                self.action_type_menu[action_type] = type_menu
            for action_widget in action_widgets:
                self.action_type_menu[action_type].addAction(action_widget)
        self.menu.triggered.connect(self.menu_triggered)

        # add other required actions
        self.menu.exec_(QtGui.QCursor.pos())

    def menu_triggered(self, action):
        '''
        Find and call the clicked function on the menu
        '''
        plugin = action.data()
        ui_callback = plugin['ui_callback']
        if hasattr(self, ui_callback):
            callback_fn = getattr(self, ui_callback)
            callback_fn(plugin)

    def ctx_update(self, plugin):
        '''
        Triggered when update action menu been clicked.
        Emits update_asset signal.
        Uses the given *plugin* to update the selected assets
        '''
        asset_info_list = []
        index_list = self.selectionModel().selectedRows()
        for index in index_list:
            data = self.model().data(index, self.model().DATA_ROLE)
            asset_info_list.append(data)

        self.update_assets.emit(asset_info_list, plugin)

    def ctx_select(self, plugin):
        '''
        Triggered when select action menu been clicked.
        Emits select_asset signal.
        '''
        asset_info_list = []
        index_list = self.selectionModel().selectedRows()
        for index in index_list:
            data = self.model().data(index, self.model().DATA_ROLE)
            asset_info_list.append(data)

        self.select_assets.emit(asset_info_list)

    def ctx_remove(self, plugin):
        '''
        Triggered when remove action menu been clicked.
        Emits remove_asset signal.
        '''
        asset_info_list = []
        index_list = []

        for model_index in self.selectionModel().selectedRows():
            index = QtCore.QPersistentModelIndex(model_index)
            index_list.append(index)

        for index in index_list:
            data = self.model().data(index, self.model().DATA_ROLE)
            asset_info_list.append(data)
        self.remove_assets.emit(asset_info_list)
    def ctx_load(self, plugin):
        #TODO: we can pass the plugin here, to for example define a standard
        # load plugin or a check plugin to execute after the load plugin that is
        # saved in the asset info is executed.
        '''
        Triggered when load action menu been clicked.
        Emits load_assets signal to load the selected assets in the scene.
        '''
        asset_info_list = []
        index_list = self.selectionModel().selectedRows()
        for index in index_list:
            data = self.model().data(index, self.model().DATA_ROLE)
            asset_info_list.append(data)

        self.load_assets.emit(asset_info_list)
    def ctx_unload(self, plugin):
        '''
        Triggered when unload action menu been clicked.
        Emits load_assets signal to unload the selected assets in the scene.
        '''
        asset_info_list = []
        index_list = self.selectionModel().selectedRows()
        for index in index_list:
            data = self.model().data(index, self.model().DATA_ROLE)
            asset_info_list.append(data)

        self.unload_assets.emit(asset_info_list)

    def set_host_connection(self, host_connection):
        '''Sets the host connection'''
        self.host_connection = host_connection
        self.asset_model.set_host_connection(self.host_connection)