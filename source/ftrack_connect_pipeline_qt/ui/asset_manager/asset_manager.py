# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from functools import partial

from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.constants import asset as asset_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetManagerBaseWidget, AssetListModel, AssetListWidget
)
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import CircularButton
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import  AccordionBaseWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import MaterialIconWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import AssetVersion as AssetVersionThumbnail
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo
from ftrack_connect_pipeline_qt.ui.utility.widget import line

class AssetManagerWidget(AssetManagerBaseWidget):
    '''Base widget of the asset manager and assembler'''
    refresh = QtCore.Signal()
    widget_status_updated = QtCore.Signal(object)
    change_asset_version = QtCore.Signal(object, object)
    select_assets = QtCore.Signal(object)
    remove_assets = QtCore.Signal(object)
    update_assets = QtCore.Signal(object, object)
    load_assets = QtCore.Signal(object)
    unload_assets = QtCore.Signal(object)

    def __init__(self, event_manager, parent=None):
        super(AssetManagerWidget, self).__init__(event_manager, parent=parent)

    def init_header_content(self, layout):
        '''Create toolbar'''
        title = QtWidgets.QLabel('Tracked assets')
        title.setStyleSheet('font-size: 14px;')
        layout.addWidget(title)
        layout.addWidget(self.init_search())
        self._refresh_button = CircularButton('sync', '#87E1EB')
        self._refresh_button.clicked.connect(self._on_refresh)
        layout.addWidget(self._refresh_button)
        self._config_button = CircularButton('cog', '#87E1EB')
        self._config_button.clicked.connect(self._on_config)
        layout.addWidget(self._config_button)

    def pre_build(self):
        super(AssetManagerWidget, self).pre_build()

    def build(self):
        super(AssetManagerWidget, self).build()

        self._asset_list = AssetListWidget(AssetListModel(self.event_manager.session), AssetWidget)

        asset_list_container = QtWidgets.QWidget()
        asset_list_container.setLayout(QtWidgets.QVBoxLayout())
        asset_list_container.layout().setContentsMargins(0,0,0,0)
        asset_list_container.layout().setSpacing(0)
        asset_list_container.layout().addWidget(self._asset_list)
        asset_list_container.layout().addWidget(QtWidgets.QLabel(''), 1000)

        self.scroll.setWidget(asset_list_container)


    def set_host_connection(self, host_connection):
        '''Sets :obj:`host_connection` with the given *host_connection*.'''
        self.host_connection = host_connection
        self._listen_widget_updates()
        #self.asset_table_view.set_host_connection(self.host_connection)

    def set_asset_list(self, asset_entities_list):
        '''Clears model and add asset entities'''
        self._asset_list.reset()
        if asset_entities_list and 0<len(asset_entities_list):
            self._asset_list.model.insertRows(0, asset_entities_list)

    def create_actions(self, actions):
        '''
        Creates all the actions for the context menu.
        '''
        self.action_widgets = {}
        # TODO: decide if to add the actions here or in the definition like the update one
        default_actions = {
            'select': [{
                'ui_callback': 'ctx_select',
                'name': 'select_asset'
            }],
            'remove': [{
                'ui_callback': 'ctx_remove',
                'name': 'remove_asset'
            }],
            'load': [{
                'ui_callback': 'ctx_load',
                'name': 'load_asset'
            }],
            'unload': [{
                'ui_callback': 'ctx_unload',
                'name': 'unload_asset'
            }]
        }
        for def_action_type, def_action in list(default_actions.items()):
            if def_action_type in list(actions.keys()):
                actions[def_action_type].extend(def_action)

        for action_type, actions in list(actions.items()):
            if action_type not in list(self.action_widgets.keys()):
                self.action_widgets[action_type] = []
            for action in actions:
                action_widget = QtWidgets.QAction(action['name'].replace('_',' ').title(), self)
                action_widget.setData(action)
                self.action_widgets[action_type].append(action_widget)

    def contextMenuEvent(self, event):
        '''Executes the context menu'''
        # Anything selected?
        widget_deselect = None
        if len(self._asset_list.get_selection(warn_on_empty=False))==0:
            # Temporaily select the clicked widget
            widget_deselect = self.childAt(event.x(), event.y())
            if widget_deselect:
                widget_deselect = widget_deselect.childAt(event.x(), event.y())
                if widget_deselect:
                    widget_deselect.header.checkbox.setChecked(True)

        self.menu = QtWidgets.QMenu(self)
        self.action_type_menu = {}
        for action_type, action_widgets in list(self.action_widgets.items()):
            if action_type not in list(self.action_type_menu.keys()):
                type_menu = QtWidgets.QMenu(action_type.title(), self)
                self.menu.addMenu(type_menu)
                self.action_type_menu[action_type] = type_menu
            for action_widget in action_widgets:
                self.action_type_menu[action_type].addAction(action_widget)
        self.menu.triggered.connect(self.menu_triggered)

        # add other required actions
        self.menu.exec_(QtGui.QCursor.pos())
        #if widget_deselect:
        #    widget_deselect.header.checkbox.setChecked(False)

    def menu_triggered(self, action):
        '''
        Find and call the clicked function on the menu
        '''
        plugin = action.data().replace(' ', '_')
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
        self.update_assets.emit(self._asset_list.get_selection(), plugin)

    def ctx_select(self, plugin):
        '''
        Triggered when select action menu been clicked.
        Emits select_asset signal.
        '''
        self.select_assets.emit(self._asset_list.get_selection())

    def ctx_remove(self, plugin):
        '''
        Triggered when remove action menu been clicked.
        Emits remove_asset signal.
        '''
        self.remove_assets.emit(self._asset_list.get_selection())

    def ctx_load(self, plugin):
        #TODO: I think is better to not pass a Plugin, and use directly the
        # function in the engine. But if we want, we can pass the plugin here,
        # to for example define a standard load plugin or a check plugin to
        # execute after the load plugin that is
        # saved in the asset info is executed.
        '''
        Triggered when load action menu been clicked.
        Emits load_assets signal to load the selected assets in the scene.
        '''
        self.load_assets.emit(self._asset_list.get_selection())

    def ctx_unload(self, plugin):
        '''
        Triggered when unload action menu been clicked.
        Emits load_assets signal to unload the selected assets in the scene.
        '''
        self.unload_assets.emit(self._asset_list.get_selection())

    def set_context_actions(self, actions):
        '''Set the :obj:`engine_type` into the asset_table_view and calls the
        create_action function of the same class with the given *actions* from definition'''
        self.engine_type = self.engine_type
        self.create_actions(actions)

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        self._asset_list.rebuild()

    def _listen_widget_updates(self):
        '''Subscribe to the PIPELINE_CLIENT_NOTIFICATION topic to call the
        _update_widget function when the host returns and answer through the
        same topic'''

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                core_constants.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._update_widget
        )

    def _on_refresh(self):
        '''Have client reload assets'''
        self.refresh.emit()

    def _on_config(self):
        pass

    def on_asset_change_version(self, index, value):
        '''
        Triggered when a version of the asset has changed on the
        :obj:`version_cb_delegate`
        '''
        _asset_info = self._asset_list.model.getData(
            index.row()
        )
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


class AssetWidget(AccordionBaseWidget):
    '''Widget representation of a minimal asset representation'''

    @property
    def index(self):
        return self._index

    @property
    def options_widget(self):
        return self._options_button

    def __init__(self, index, session, title=None, checkable=False, parent=None):
        super(AssetWidget, self).__init__(session=session, title=title, checkable=checkable, checked=False, parent=parent)
        self._version_id = None
        self._index = index

    def init_status_icon(self):
        self._status_icon = MaterialIconWidget(None)
        self._status_icon.setObjectName('borderless')
        return self._status_icon

    def init_header_content(self, header_layout, collapsed):
        '''Add publish related widgets to the accordion header'''
        header_layout.setContentsMargins(1, 1, 1, 1)
        header_layout.setSpacing(2)
        self._asset_name_widget = QtWidgets.QLabel()
        header_layout.addWidget(self._asset_name_widget)
        self._version_selector = AssetVersionSelector()
        header_layout.addWidget(self._version_selector)
        header_layout.addStretch()
        header_layout.addWidget(self.init_status_icon())

    def init_content(self, content_layout):
        self.content.setMinimumHeight(200)
        content_layout.setContentsMargins(10, 2, 10, 2)

    def update(self, asset_info):
        '''Update widget from data'''
        # ({'asset_id': 'db4ad014-5b76-434b-8a0f-ab6ae979ef4d', 'asset_name': 'uploadasset', 'asset_type_name': 'Upload', 'version_id': '1720f6f3-4854-4796-a2ce-fe225178bf49', 'version_number': 2, 'component_path': '/Volumes/AccsynStorage/accsynftrackpoc/sq010/sh030/_PUBLISH/generic/v002/main.mp4', 'component_name': 'main', 'component_id': 'a07e3c4a-8f51-4492-bc97-04a54cf94fbb', 'load_mode': None, 'asset_info_options': None, 'reference_object': None, 'is_latest_version': True, 'asset_versions_entities': None, 'session': <ftrack_api.session.Session object at 0x10b527250>, 'asset_info_id': '38bb6b0442014a278181d335abe5124a', 'dependency_ids': [], 'is_dependency': False, 'dependencies': None, 'context_name': 'sh030'})
        self._version_id = asset_info[asset_constants.VERSION_ID]
        self._asset_name_widget.setText('{} - '.format(asset_info[asset_constants.ASSET_NAME]))
        self._version_selector.clear()
        versions_collection = asset_info[asset_constants.ASSET_VERSIONS_ENTITIES]
        for asset_version in versions_collection:
            self._version_selector.addItem('v{}'.format(asset_version['version']), asset_version['id'])
        self._status_icon.set_icon('check' if not asset_info[asset_constants.LOAD_MODE] is None else 'close',
                                   color = '#87E1EB' if not asset_info[asset_constants.LOAD_MODE] is None else '#999999')
        self._version_dependency_ids = asset_info[asset_constants.DEPENDENCY_IDS]

    def on_collapse(self, collapsed):
        '''Dynamically populate asset expanded view'''
        #Remove all content widgets
        for i in reversed(range(self.content.layout().count())):
            widget = self.content.layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if collapsed is False:
            if self._version_id is None:
                self.add_widget(QtWidgets.QLabel('Have no version ID!'))
                version = None
            else:
                version = self.session.query('AssetVersion where id={}'.format(self._version_id)).one()

            self.add_widget(QtWidgets.QLabel('Context:'))

            context_widget = QtWidgets.QWidget()
            context_widget.setLayout(QtWidgets.QHBoxLayout())
            context_widget.setContentsMargins(1, 1, 1, 1)
            context_widget.setMaximumHeight(64)

            if version:
                # Add thumbnail
                self._thumbnail_widget = AssetVersionThumbnail(self.session)
                self._thumbnail_widget.load(self._version_id)
                self._thumbnail_widget.setScaledContents(True)
                self._thumbnail_widget.setMinimumSize(69, 48)
                self._thumbnail_widget.setMaximumSize(69, 48)
                context_widget.layout().addWidget(self._thumbnail_widget)

                # Add context info
                self._entity_info = EntityInfo()
                self._entity_info.set_entity(version['asset']['parent'])
                self._entity_info.setMinimumHeight(100)
                context_widget.layout().addWidget(self._entity_info, 100)
                #context_widget.layout().addWidget(QtWidgets.QLabel('Test'))

            self.add_widget(context_widget)

            self.add_widget(line.Line())

            self.add_widget(QtWidgets.QLabel('Dependencies:'))

            for dep_version_id in (self._version_dependency_ids or []):
                dep_version = self.session.query('AssetVersion where id={}'.format(dep_version_id)).first()

                if dep_version:
                    dep_version_widget = QtWidgets.QWidget()
                    dep_version_widget.setLayout(QtWidgets.QHBoxLayout())
                    dep_version_widget.setContentsMargins(15, 1, 1, 1)
                    dep_version_widget.setMaximumHeight(64)

                    dep_thumbnail_widget = AssetVersionThumbnail(self.session)
                    dep_thumbnail_widget.load(dep_version_id)
                    dep_thumbnail_widget.setScaledContents(True)
                    dep_thumbnail_widget.setMinimumSize(69, 48)
                    dep_thumbnail_widget.setMaximumSize(69, 48)
                    dep_version_widget.layout().addWidget(dep_thumbnail_widget)

                    # Add context info
                    dep_entity_info = EntityInfo()
                    dep_entity_info.set_entity(version['asset']['parent'])
                    dep_entity_info.setMinimumHeight(100)
                    context_widget.layout().addWidget(dep_entity_info, 100)
                    # context_widget.layout().addWidget(QtWidgets.QLabel('Test'))

                    self.add_widget(dep_version_widget)
                else:
                    self.add_widget(QtWidgets.QLabel('MISSING dependency version: {}'.format(dep_version_id)))

            self.add_widget(line.Line())

            self.add_widget(QtWidgets.QLabel('Load options:'))


    def update_input(self, message, status):
        '''Update the accordion input summary, should be overridden by child.'''
        pass


class AssetVersionSelector(QtWidgets.QComboBox):
    def __init__(self):
        super(AssetVersionSelector, self).__init__()
        #self.setMinimumWidth(150)