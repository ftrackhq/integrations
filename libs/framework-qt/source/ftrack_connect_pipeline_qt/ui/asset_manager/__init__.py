# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
from functools import partial


from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.constants import asset as asset_constants
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetManagerBaseWidget,
    AssetListWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline_qt.utils import set_property
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    AssetVersion as AssetVersionThumbnail,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo
from ftrack_connect_pipeline_qt.ui.utility.widget import line
from ftrack_connect_pipeline_qt.utils import clear_layout
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import ModalDialog
from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.button import ApproveButton


class AssetManagerWidget(AssetManagerBaseWidget):
    '''Asset manager widget that lives within the asset manager client'''

    refresh = QtCore.Signal()  # Refresh asset list from model
    rebuild = QtCore.Signal()  # Fetch assets from DCC and update model

    changeAssetVersion = QtCore.Signal(
        object, object
    )  # User has requested a change of asset version
    selectAssets = QtCore.Signal(object, object)  # Select assets in DCC
    removeAssets = QtCore.Signal(object, object)  # Remove assets from DCC
    updateAssets = QtCore.Signal(
        object, object
    )  # Update DCC assets to latest version
    loadAssets = QtCore.Signal(object, object)  # Load assets into DCC
    unloadAssets = QtCore.Signal(object, object)  # Unload assets from DCC

    stopBusyIndicator = QtCore.Signal()  # Stop spinner and hide it

    DEFAULT_ACTIONS = {
        'select': [{'ui_callback': 'ctx_select', 'name': 'select_asset'}],
        'remove': [{'ui_callback': 'ctx_remove', 'name': 'remove_asset'}],
        'load': [{'ui_callback': 'ctx_load', 'name': 'load_asset'}],
        'unload': [{'ui_callback': 'ctx_unload', 'name': 'unload_asset'}],
    }

    @property
    def asset_list(self):
        '''Return asset list widget'''
        return self._asset_list

    @property
    def host_connection(self):
        '''Return the host connection'''
        return self._client.host_connection

    def __init__(self, asset_manager_client, asset_list_model, parent=None):
        '''
        Initialize the asset manager widget

        :param asset_manager_client: :class:`~ftrack_connect_pipeline_qt.client.asset_manager.QtAssetManagerClient` instance
        :param asset_list_model: : instance of :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.model.AssetListModel`
        :param parent:  The parent dialog or window
        '''
        self._client = asset_manager_client
        self.client_notification_subscribe_id = None
        super(AssetManagerWidget, self).__init__(
            asset_manager_client.is_assembler,
            asset_manager_client.event_manager,
            asset_list_model,
            parent=parent,
        )

    def _build_docked_header(self, layout):
        '''Build DCC docked header and add to *layout*'''
        row1 = QtWidgets.QWidget()
        row1.setLayout(QtWidgets.QHBoxLayout())
        row1.layout().setContentsMargins(5, 5, 5, 5)
        row1.layout().setSpacing(6)

        title = QtWidgets.QLabel('Tracked assets')
        title.setObjectName('h2')
        row1.layout().addWidget(title)

        row1.layout().addWidget(QtWidgets.QLabel(), 10)

        self._config_button = ApproveButton('ADD / REMOVE ASSETS')
        self._config_button.clicked.connect(self._on_config)
        row1.layout().addWidget(self._config_button)

        layout.addWidget(row1)

        row2 = QtWidgets.QWidget()
        row2.setLayout(QtWidgets.QHBoxLayout())
        row2.layout().setContentsMargins(5, 5, 5, 5)
        row2.layout().setSpacing(6)

        row2.layout().addWidget(self.init_search())

        self._rebuild_button = CircularButton('sync')
        row2.layout().addWidget(self._rebuild_button)

        self._busy_widget = BusyIndicator(start=False)
        self._busy_widget.setMinimumSize(QtCore.QSize(24, 24))
        self._busy_widget.setVisible(False)
        row2.layout().addWidget(self._busy_widget)

        layout.addWidget(row2)

    def _build_assembler_header(self, layout):
        '''Build assembler docked header and add to *layout*'''
        row1 = QtWidgets.QWidget()
        row1.setLayout(QtWidgets.QHBoxLayout())
        row1.layout().setContentsMargins(5, 5, 5, 5)
        row1.layout().setSpacing(6)
        row1.setMinimumHeight(52)

        title = QtWidgets.QLabel('Tracked assets')
        title.setObjectName('h2')
        row1.layout().addWidget(title)

        layout.addWidget(row1)

        row2 = QtWidgets.QWidget()
        row2.setLayout(QtWidgets.QHBoxLayout())
        row2.layout().setContentsMargins(5, 5, 5, 5)
        row2.layout().setSpacing(6)

        row2.layout().addWidget(QtWidgets.QLabel(), 10)

        self._label_info = QtWidgets.QLabel('Listing 0 assets')
        self._label_info.setObjectName('gray')
        row2.layout().addWidget(self._label_info)

        row2.layout().addWidget(self.init_search())

        self._rebuild_button = CircularButton('sync')
        row2.layout().addWidget(self._rebuild_button)

        self._busy_widget = BusyIndicator(start=False)
        self._busy_widget.setMinimumSize(QtCore.QSize(16, 16))
        row2.layout().addWidget(self._busy_widget)
        self._busy_widget.setVisible(False)

        layout.addWidget(row2)

    def build_header(self, layout):
        '''(Override)'''
        self._build_docked_header(
            layout
        ) if not self._is_assembler else self._build_assembler_header(layout)

    def build(self):
        '''(Override)'''
        super(AssetManagerWidget, self).build()

        self._asset_list = AssetManagerListWidget(
            self._asset_list_model,
            AssetWidget,
            docked=self._client.is_docked(),
        )

        asset_list_container = QtWidgets.QWidget()
        asset_list_container.setLayout(QtWidgets.QVBoxLayout())
        asset_list_container.layout().setContentsMargins(0, 0, 0, 0)
        asset_list_container.layout().setSpacing(0)
        asset_list_container.layout().addWidget(self._asset_list)
        asset_list_container.layout().addWidget(QtWidgets.QLabel(''), 1000)

        self.scroll.setWidget(asset_list_container)

    def post_build(self):
        '''(Override)'''
        super(AssetManagerWidget, self).post_build()
        self._rebuild_button.clicked.connect(self._on_rebuild)
        self.refresh.connect(self._on_refresh)
        self.stopBusyIndicator.connect(self._on_stop_busy_indicator)
        self._asset_list.refreshed.connect(self._on_asset_list_refreshed)
        self._asset_list.changeAssetVersion.connect(
            self._on_change_asset_version
        )

    def set_asset_list(self, asset_entities_list):
        '''Clear model and add asset entities, will trigger list to be rebuilt.'''
        self._asset_list_model.reset()
        if asset_entities_list and 0 < len(asset_entities_list):
            self._asset_list.model.insertRows(0, asset_entities_list)

    def set_busy(self, busy):
        '''Enter busy mode if *busy* is True - start spinner and show it. If *busy* is false, stop and hide the spinner'''
        if busy:
            self._busy_widget.start()
            self._rebuild_button.setVisible(False)
            self._busy_widget.setVisible(True)
        else:
            self._busy_widget.stop()
            self._busy_widget.setVisible(False)
            self._rebuild_button.setVisible(True)

    def _on_stop_busy_indicator(self):
        '''Stop spinner callback from background thread'''
        self.set_busy(False)

    def on_search(self, text):
        '''Search text has been altered by user, search in the current model and hide assets accordingly'''
        if self._asset_list:
            self._asset_list.on_search(text)

    def create_actions(self, actions):
        '''Creates all the actions for the context menu.'''
        self.action_widgets = {}
        # TODO: decide if to add the actions here or in the definition like the
        #  update one
        for def_action_type, def_action in list(self.DEFAULT_ACTIONS.items()):
            if def_action_type in list(actions.keys()):
                actions[def_action_type].extend(def_action)

        for action_type, actions in list(actions.items()):
            if action_type not in list(self.action_widgets.keys()):
                self.action_widgets[action_type] = []
            for action in actions:
                action_widget = QtWidgets.QAction(
                    action['name'].replace('_', ' ').title(), self
                )
                action_widget.setData(action)
                self.action_widgets[action_type].append(action_widget)

    def contextMenuEvent(self, event):
        '''Executes the context menu'''
        # Anything selected?
        widget_deselect = None
        if len(self._asset_list.selection()) == 0:
            # Select the clicked widget
            widget_select = self.childAt(event.x(), event.y())
            if widget_select:
                widget_select = widget_select.childAt(event.x(), event.y())
                if widget_select:
                    widget_select.setSelected(True)

        self.menu = QtWidgets.QMenu(self)
        self.action_type_menu = {}
        for action_type, action_widgets in list(self.action_widgets.items()):
            if not self._is_assembler and action_type == 'remove':
                continue  # Can only remove from is_assembler
            if action_type not in list(self.action_type_menu.keys()):
                type_menu = QtWidgets.QMenu(action_type.title(), self)
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
        # plugin['name'].replace(' ', '_')
        ui_callback = plugin['ui_callback']
        if hasattr(self, ui_callback):
            callback_fn = getattr(self, ui_callback)
            callback_fn(plugin)

    def check_selection(self, selected_assets):
        '''Check if *selected_assets* is empty and show dialog message'''
        if len(selected_assets) == 0:
            ModalDialog(
                self._client,
                title='Error!',
                message="Please select at least one asset!",
            )
            return False
        else:
            return True

    def ctx_select(self, plugin):
        '''
        Triggered when select action menu been clicked.
        Emits select_asset signal.
        '''
        selection = self._asset_list.selection()
        if self.check_selection(selection):
            self.selectAssets.emit(selection, plugin)

    def ctx_load(self, plugin):
        '''
        Triggered when load action menu been clicked.
        Emits load_assets signal to load the selected assets in the scene.
        '''
        selection = self._asset_list.selection()
        if self.check_selection(selection):
            for a_info in selection:
                loaded = a_info[asset_constants.OBJECTS_LOADED]
                # This is not always a boolean so that is why ensuring the
                # correct behaviour using str.
                if str(loaded) == "True":
                    selection.remove(a_info)
            if len(selection) == 0:
                ModalDialog(
                    self._client,
                    title='ftrack Asset manager',
                    message='Selected Assets are already loaded.',
                )
            else:
                self.loadAssets.emit(selection, plugin)

    def ctx_update(self, plugin):
        '''
        Triggered when update action menu been clicked.
        Emits update_asset signal.
        Uses the given *plugin* to update the selected assets
        '''
        selection = self._asset_list.selection()
        if self.check_selection(selection):
            if ModalDialog(
                self._client.parent(),
                title='ftrack Asset manager',
                question='Really update {} asset{} to latest version?'.format(
                    len(selection), 's' if len(selection) > 1 else ''
                ),
            ).exec_():
                self.updateAssets.emit(selection, plugin)

    def ctx_unload(self, plugin):
        '''
        Triggered when unload action menu been clicked.
        Emits load_assets signal to unload the selected assets in the scene.
        '''
        selection = self._asset_list.selection()
        if self.check_selection(selection):
            for a_info in selection:
                loaded = a_info[asset_constants.OBJECTS_LOADED]
                # This is not always a boolean so that is why ensuring the
                # correct behaviour using str.
                if str(loaded) == "False":
                    selection.remove(a_info)
            if len(selection) == 0:
                ModalDialog(
                    self._client,
                    title='ftrack Asset manager',
                    message='Selected Assets are already unloaded.',
                )
            else:
                if ModalDialog(
                    self._client.parent(),
                    title='ftrack Asset manager',
                    question='Really unload {} asset{}?'.format(
                        len(selection), 's' if len(selection) > 1 else ''
                    ),
                ).exec_():
                    self.unloadAssets.emit(selection, plugin)

    def ctx_remove(self, plugin):
        '''
        Triggered when remove action menu been clicked.
        Emits remove_asset signal.
        '''
        selection = self._asset_list.selection()
        if self.check_selection(selection):
            if ModalDialog(
                self._client.parent(),
                title='ftrack Asset manager',
                question='Really remove {} asset{}?'.format(
                    len(selection), 's' if len(selection) > 1 else ''
                ),
            ).exec_():
                self.removeAssets.emit(selection, plugin)

    def set_context_actions(self, actions):
        '''Set the :obj:`engine_type` into the asset_table_view and calls the
        create_action function of the same class with the given *actions* from
        definition'''
        self.engine_type = self.engine_type
        self.create_actions(actions)

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        # Check if this is a asset discover notification
        if event['data']['pipeline'].get('method') == 'discover_assets':
            # This could be executed async, rebuild asset list through signal
            self.rebuild.emit()

    def _listen_widget_updates(self):
        '''Subscribe to the PIPELINE_CLIENT_NOTIFICATION topic to call the
        _update_widget function when the host returns and answer through the
        same topic'''

        self.client_notification_subscribe_id = (
            self.session.event_hub.subscribe(
                'topic={} and data.pipeline.host_id={}'.format(
                    core_constants.PIPELINE_CLIENT_NOTIFICATION,
                    self.host_connection.id,
                ),
                self._update_widget,
            )
        )

    def _on_refresh(self):
        '''Refresh the asset list from the model data.'''
        self._asset_list.rebuild()

    def _on_asset_list_refreshed(self):
        '''List has refreshed from model'''
        if self._is_assembler:
            self._label_info.setText(
                'Listing {} asset{}'.format(
                    self._asset_list.model.rowCount(),
                    's' if self._asset_list.model.rowCount() > 1 else '',
                )
            )
        self._client.selectionUpdated.emit(self._asset_list.selection())

    def _on_rebuild(self):
        '''Query DCC for scene assets.'''
        self.rebuild.emit()  # To be picked up by AM

    def _on_config(self):
        '''Callback when user wants to open the assembler'''
        self.host_connection.launch_client(qt_constants.ASSEMBLER_WIDGET)

    def _on_add(self):
        '''Callback when user wants to add and asset'''
        self.host_connection.launch_client(qt_constants.ASSEMBLER_WIDGET)

    def _on_change_asset_version(self, asset_info, version_entity):
        '''
        Triggered when a version of the asset has changed on the
        :obj:`version_cb_delegate`. Prompt user.
        '''
        self.changeAssetVersion.emit(asset_info.copy(), version_entity['id'])


class AssetManagerListWidget(AssetListWidget):
    '''Custom asset manager list view widget'''

    changeAssetVersion = QtCore.Signal(
        object, object
    )  # User has commanded a change of version

    def __init__(self, model, asset_widget_class, docked=False, parent=None):
        '''
        Initialize the asset manager list widget

        :param model: :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.model.AssetListModel` instance
        :param asset_widget_class: The class inheriting from :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.AssetWidget` to use when instantiating assets
        :param docked: Boolean telling if the list is docked in DCC or is within an ftrack dialog - drive style
        :param parent: The parent dialog or frame
        '''
        self._asset_widget_class = asset_widget_class
        self._docked = docked
        self.prev_search_text = ''

        super(AssetManagerListWidget, self).__init__(model, parent=parent)

    def post_build(self):
        '''(Override)'''
        super(AssetManagerListWidget, self).post_build()
        # Do not distinguish between different model events,
        # always rebuild entire list from scratch for now.
        self._model.rowsInserted.connect(self._on_asset_data_changed)
        self._model.modelReset.connect(self._on_asset_data_changed)
        self._model.rowsRemoved.connect(self._on_asset_data_changed)
        self._model.dataChanged.connect(self._on_asset_data_changed)

    def _on_asset_data_changed(self, *args):
        '''React upon change in asset model'''
        self.rebuild()

    def rebuild(
        self,
    ):
        '''Clear widget and add all assets again from model.'''
        clear_layout(self.layout())
        # TODO: Save selection state
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)
            asset_info = self.model.data(index)
            asset_widget = self._asset_widget_class(
                index, self.model.event_manager, docked=self._docked
            )
            set_property(
                asset_widget, 'first', 'true' if row == 0 else 'false'
            )
            asset_widget.set_asset_info(asset_info)
            self.layout().addWidget(asset_widget)
            asset_widget.clicked.connect(
                partial(self.asset_clicked, asset_widget)
            )
            asset_widget.changeAssetVersion.connect(
                self._on_change_asset_version
            )
        self.refresh()
        self.refreshed.emit()

    def _on_change_asset_version(self, index, version_entity):
        '''User has commanded a change of version within the asset, propagate'''
        self.changeAssetVersion.emit(self.model.data(index), version_entity)

    def refresh(self, search_text=None):
        '''Update asset list depending on search text'''
        if search_text is None:
            search_text = self.prev_search_text
        for asset_widget in self.assets:
            asset_widget.setVisible(
                len(search_text) == 0 or asset_widget.matches(search_text)
            )

    def on_search(self, text):
        '''Callback on change of user search input'''
        if text != self.prev_search_text:
            self.refresh(text.lower())
            self.prev_search_text = text


class AssetWidget(AccordionBaseWidget):
    '''Minimal widget representation of an asset(asset_info)'''

    changeAssetVersion = QtCore.Signal(object, object)  # User change version

    @property
    def index(self):
        '''Return the index this asset has in list'''
        return self._index

    @property
    def options_widget(self):
        '''Return the widget representing options'''
        return self._options_button

    def __init__(self, index, event_manager, docked=False, parent=None):
        '''
        Initialize asset widget

        :param index: The index this asset has in list
        :param event_manager:  :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param docked: Boolean telling if the list is docked in DCC or is within an ftrack dialog - drive style
        :param parent: The parent dialog or frame
        '''
        super(AssetWidget, self).__init__(
            AccordionBaseWidget.SELECT_MODE_LIST,
            AccordionBaseWidget.CHECK_MODE_NONE,
            event_manager=event_manager,
            checked=False,
            docked=docked,
            parent=parent,
        )
        self._version_id = None
        self._index = index

    def init_status_widget(self):
        '''Build the asset status widget'''
        self._status_widget = AssetVersionStatusWidget()
        return self._status_widget

    def init_header_content(self, header_widget, collapsed):
        '''Build asset widgets and add to the accordion header'''
        header_layout = QtWidgets.QHBoxLayout()
        header_widget.setLayout(header_layout)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(5, 1, 0, 1)
        header_layout.setSpacing(0)

        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())
        widget.layout().setContentsMargins(0, 0, 0, 0)
        widget.layout().setSpacing(2)

        # Add context path, relative to browser context
        self._path_widget = QtWidgets.QLabel()
        self._path_widget.setStyleSheet('font-size: 9px;')
        self._path_widget.setObjectName("gray-dark")

        widget.layout().addWidget(self._path_widget)

        lower_widget = QtWidgets.QWidget()
        lower_widget.setLayout(QtWidgets.QHBoxLayout())
        lower_widget.layout().setContentsMargins(0, 0, 0, 0)
        lower_widget.layout().setSpacing(0)

        self._asset_name_widget = QtWidgets.QLabel()
        self._asset_name_widget.setObjectName('h4')
        lower_widget.layout().addWidget(self._asset_name_widget)
        self._component_and_version_header_widget = ComponentAndVersionWidget(
            True
        )
        lower_widget.layout().addWidget(
            self._component_and_version_header_widget
        )

        delimiter_label = QtWidgets.QLabel(' - ')
        delimiter_label.setObjectName('gray')
        lower_widget.layout().addWidget(delimiter_label)

        lower_widget.layout().addWidget(self.init_status_widget())

        lower_widget.layout().addWidget(QtWidgets.QLabel(), 10)

        widget.layout().addWidget(lower_widget)

        header_layout.addWidget(widget)

    def init_content(self, content_layout):
        '''(Override) Initialize the accordion content'''
        content_layout.setContentsMargins(10, 2, 10, 2)
        content_layout.setSpacing(5)

    def set_asset_info(self, asset_info):
        '''Update widget from asset data provided in *asset_info*'''
        self._version_id = asset_info[asset_constants.VERSION_ID]
        version = self.session.query(
            'select is_latest_version from AssetVersion where id={}'.format(
                self._version_id
            )
        ).one()
        # Calculate path
        parent_path = [link['name'] for link in version['task']['link']]
        self._path_widget.setText(' / '.join(parent_path))
        self._asset_name_widget.setText(
            '{} '.format(asset_info[asset_constants.ASSET_NAME])
        )

        query = (
            'select is_latest_version, id, asset, components, components.name, '
            'components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}"'
            'order by version ascending'
        ).format(
            asset_info[asset_constants.ASSET_ID],
            asset_info[asset_constants.COMPONENT_NAME],
        )
        versions = self.session.query(query).all()

        self._versions_collection = versions
        self._version_nr = version['version']
        self._status_widget.set_status(version['status'])
        self._load_mode = asset_info[asset_constants.LOAD_MODE]

        indicator_color = 'gray'
        self._is_loaded = asset_info.get(asset_constants.OBJECTS_LOADED)
        self._is_latest_version = version['is_latest_version']
        if self._is_loaded:
            if self._is_latest_version:
                indicator_color = 'green'
            else:
                indicator_color = 'orange'
                self.setToolTip(
                    'There is a newer version available for this asset, right click and run "Update" to update it.'
                )
        self.set_indicator_color(indicator_color)
        self._component_path = (
            asset_info[asset_constants.COMPONENT_NAME] or '?.?'
        )
        self._component_and_version_header_widget.set_component_filename(
            self._component_path
        )
        self._component_and_version_header_widget.set_version(
            asset_info[asset_constants.VERSION_NUMBER]
        )
        self._component_and_version_header_widget.set_latest_version(
            self._is_latest_version
        )
        self._load_mode = asset_info[asset_constants.LOAD_MODE]
        self._asset_info_options = asset_info[
            asset_constants.ASSET_INFO_OPTIONS
        ]
        # Info
        self._published_by = version['user']
        self._published_date = version['date']
        # Deps
        self._version_dependency_ids = asset_info[
            asset_constants.DEPENDENCY_IDS
        ]

    def matches(self, search_text):
        '''Do a simple match if this search text matches any asset attributes'''
        if self._path_widget.text().lower().find(search_text) > -1:
            return True
        if self._asset_name_widget.text().lower().find(search_text) > -1:
            return True
        if (self._component_path or '').lower().find(search_text) > -1:
            return True
        if (
            '{} {} {}'.format(
                self._published_by['first_name'],
                self._published_by['last_name'],
                self._published_by['email'],
            )
        ).lower().find(search_text) > -1:
            return True
        return False

    def on_collapse(self, collapsed):
        '''Dynamically populate asset expanded view'''
        # Remove all content widgets
        for i in reversed(range(self.content.layout().count())):
            widget = self.content.layout().itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if collapsed is False:
            if self._version_id is None:
                self.add_widget(QtWidgets.QLabel('Have no version ID!'))
                version = None
            else:
                version = self.session.query(
                    'AssetVersion where id={}'.format(self._version_id)
                ).one()

            context_widget = QtWidgets.QWidget()
            context_widget.setLayout(QtWidgets.QHBoxLayout())
            context_widget.layout().setContentsMargins(1, 3, 1, 3)
            context_widget.setMaximumHeight(64)

            if version:
                # Add thumbnail
                self._thumbnail_widget = AssetVersionThumbnail(self.session)
                self._thumbnail_widget.load(self._version_id)
                self._thumbnail_widget.setScaledContents(True)
                self._thumbnail_widget.setMinimumHeight(50)
                self._thumbnail_widget.setMaximumHeight(50)
                self._thumbnail_widget.setMinimumWidth(90)
                self._thumbnail_widget.setMaximumWidth(90)
                context_widget.layout().addWidget(self._thumbnail_widget)

                self._component_and_version_widget = ComponentAndVersionWidget(
                    False
                )
                self._component_and_version_widget.set_component_filename(
                    self._component_path
                )
                self._component_and_version_widget.set_version(
                    self._version_nr, versions=self._versions_collection
                )
                self._component_and_version_widget.set_latest_version(
                    self._is_latest_version
                )
                self._component_and_version_widget.version_selector.currentIndexChanged.connect(
                    self._on_version_selected
                )

                # Add context info with version selection
                self._entity_info = EntityInfo(
                    additional_widget=self._component_and_version_widget
                )
                self._entity_info.entity = version['task']['parent']
                self._entity_info.setMinimumHeight(100)
                context_widget.layout().addWidget(self._entity_info, 100)

            self.add_widget(context_widget)

            load_info_label = QtWidgets.QLabel(
                '<html>Added as a <font color="white">{}</font> with <font color="white">'
                '{}</font></html>'.format(
                    self._load_mode,
                    self._asset_info_options.get('pipeline', {}).get(
                        'definition', '?'
                    )
                    if self._asset_info_options
                    else '?',
                )
            )
            self.add_widget(load_info_label)
            load_info_label.setToolTip(
                json.dumps(self._asset_info_options, indent=2)
            )
            self.add_widget(
                QtWidgets.QLabel(
                    '<html>Published by: <font color="white">{} {}</font></html>'.format(
                        self._published_by['first_name'],
                        self._published_by['last_name'],
                    )
                )
            )
            self.add_widget(
                QtWidgets.QLabel(
                    '<html>Publish date: <font color="white">{}</font></html>'.format(
                        self._published_date
                    )
                )
            )

            if 0 < len(self._version_dependency_ids or []):
                self.add_widget(line.Line())

                dependencies_label = QtWidgets.QLabel(
                    'DEPENDENCIES({}):'.format(
                        len(self._version_dependency_ids)
                    )
                )
                dependencies_label.setObjectName('h4')
                self.add_widget(dependencies_label)

                for dep_version_id in self._version_dependency_ids:
                    dep_version = self.session.query(
                        'AssetVersion where id={}'.format(dep_version_id)
                    ).first()

                    if dep_version:
                        dep_version_widget = QtWidgets.QWidget()
                        dep_version_widget.setLayout(QtWidgets.QHBoxLayout())
                        dep_version_widget.setContentsMargins(20, 1, 1, 1)
                        dep_version_widget.setMaximumHeight(64)

                        dep_thumbnail_widget = AssetVersionThumbnail(
                            self.session
                        )
                        dep_thumbnail_widget.load(dep_version_id)
                        dep_thumbnail_widget.setScaledContents(True)
                        dep_thumbnail_widget.setMinimumSize(69, 48)
                        dep_thumbnail_widget.setMaximumSize(69, 48)
                        dep_version_widget.layout().addWidget(
                            dep_thumbnail_widget
                        )

                        # Add context info
                        dep_entity_info = EntityInfo(
                            additional_widget=QtWidgets.QLabel(
                                ' - v{}'.format(dep_version['version'])
                            )
                        )
                        dep_entity_info.entity = dep_version['task']
                        dep_entity_info.setMinimumHeight(100)
                        dep_version_widget.layout().addWidget(dep_entity_info)

                        self.add_widget(dep_version_widget)
                    else:
                        self.add_widget(
                            QtWidgets.QLabel(
                                'MISSING dependency '
                                'version: {}'.format(dep_version_id)
                            )
                        )

                self.add_widget(line.Line())

            self.content.layout().addStretch()

    def _on_version_selected(self, index):
        '''Change version of asset.'''
        version = self.session.query(
            'AssetVersion where id={}'.format(
                self._component_and_version_widget.version_selector.itemData(
                    index
                )
            )
        ).first()
        if version['id'] != self._version_id:
            current_version = self.session.query(
                'AssetVersion where id={}'.format(self._version_id)
            ).first()
            if ModalDialog(
                None,
                title='ftrack Asset manager',
                question='Change version of {} to v{}?'.format(
                    str_version(current_version), version['version']
                ),
            ).exec_():
                self.changeAssetVersion.emit(self.index, version)
            else:
                # Revert back
                self._component_and_version_widget.set_version(
                    current_version['version']
                )


class AssetVersionStatusWidget(QtWidgets.QFrame):
    '''Widget representing static asset state'''

    def __init__(self, bordered=True):
        super(AssetVersionStatusWidget, self).__init__()
        self._bordered = bordered

        self.pre_build()
        self.build()
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(4, 2, 4, 2)
        self.layout().setSpacing(4)

    def build(self):
        self._label_widget = QtWidgets.QLabel()
        if self._bordered:
            self._label_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.layout().addWidget(self._label_widget)

    def set_status(self, status):
        self._label_widget.setText(status['name'].upper())
        self._label_widget.setStyleSheet(
            '''
            color: {0};
            border: none;
        '''.format(
                status['color']
            )
        )


class AssetVersionSelector(QtWidgets.QComboBox):
    '''Widget representing dynamic asset state modifiable by user'''

    def __init__(self):
        super(AssetVersionSelector, self).__init__()
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)


class ComponentAndVersionWidget(QtWidgets.QWidget):
    '''Widget representing the asset component and version'''

    @property
    def version_selector(self):
        return self._version_selector

    def __init__(self, collapsed, parent=None):
        '''
        Initialize component & version widget

        :param collapsed: Boolean telling if widget is within collapsed accordion or not
        :param parent: the parent dialog or frame
        '''
        super(ComponentAndVersionWidget, self).__init__(parent=parent)

        self._collapsed = collapsed

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(2)

    def build(self):
        self._component_filename_widget = QtWidgets.QLabel()
        self._component_filename_widget.setObjectName('gray')
        self.layout().addWidget(self._component_filename_widget)
        delimiter_label = QtWidgets.QLabel(' - ')
        delimiter_label.setObjectName('gray')
        self.layout().addWidget(delimiter_label)

        if self._collapsed:
            self._version_nr_widget = QtWidgets.QLabel()
            self._version_nr_widget.setObjectName('color-primary')
            self.layout().addWidget(self._version_nr_widget)
        else:
            self._version_selector = AssetVersionSelector()
            self.layout().addWidget(self._version_selector)

    def set_latest_version(self, is_latest_version):
        '''Set if asset version is the latest version (*is_latest_version* is True) or not'''
        color = '#A5A8AA' if is_latest_version else '#FFBA5C'
        if self._collapsed:
            self._version_nr_widget.setStyleSheet('color: {}'.format(color))
        else:
            self.version_selector.setStyleSheet(
                '''
                color: {0};
                border: 1px solid {0};
            '''.format(
                    color
                )
            )

    def set_component_filename(self, component_path):
        '''Set the component filename based on *component_path*'''
        self._component_filename_widget.setText(
            '- {}'.format(component_path.replace('\\', '/').split('/')[-1])
        )

    def set_version(self, version_nr, versions=None):
        '''Set the current version number from *version_nr*. *versions* should
        be provided if about to expand, otherwise the version will be selected
        '''
        if self._collapsed:
            self._version_nr_widget.setText('v{}'.format(str(version_nr)))
        else:
            if versions:
                self.version_selector.clear()
                for index, asset_version in enumerate(reversed(versions)):
                    self.version_selector.addItem(
                        'v{}'.format(asset_version['version']),
                        asset_version['id'],
                    )
                    if asset_version['version'] == version_nr:
                        self.version_selector.setCurrentIndex(index)
            else:
                label = 'v{}'.format(version_nr)
                for index in range(self.version_selector.count()):
                    if self.version_selector.itemText(index) == label:
                        self.version_selector.setCurrentIndex(index)
                        break
