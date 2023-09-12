# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.accordion import AssetAccordionWidget
from ftrack_qt.widgets.model import AssetInfoListModel
from ftrack_qt.widgets.dialogs import ModalDialog
from ftrack_qt.widgets.search import SearchBox
from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.buttons import ApproveButton, CircularButton
from ftrack_qt.widgets.overlay import BusyIndicator

logger = logging.getLogger(__name__)


class AssetManagerBrowser(QtWidgets.QWidget):
    '''Widget for browsing amd modifying assets loaded within a DCC'''

    remove_enabled = False  # Disable remove of assets by default

    # Signals

    refresh = QtCore.Signal()
    # Asset list has been refreshed

    change_asset_version = QtCore.Signal(object, object)
    # User has requested a change of asset version

    on_config = QtCore.Signal()
    # User has requested to configure assets

    stop_busy_indicator = QtCore.Signal()
    # Stop spinner and hide it

    run_plugin = QtCore.Signal(object, object, object)
    # Run plugin with *plugin_definition*, *plugin_method_nam* and *callback*

    @property
    def framework_dialog(self):
        '''Returns framework_dialog'''
        return self._framework_dialog

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self.framework_dialog.event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def __init__(self, framework_dialog, parent=None):
        '''Instantiate the browser within parent *framework_dialog*'''
        super(AssetManagerBrowser, self).__init__(parent=parent)
        self._framework_dialog = framework_dialog
        self._asset_list_model = AssetInfoListModel()
        self._discovery_plugin_definition = None

        self._action_widgets = None
        self._config_button = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def _build_asset_widget(self, index, asset_info):
        '''Factory creating an asset widget for *index* and *asset_info*.'''
        # result = AssetAccordionWidget(index, self.event_manager)
        result = self.framework_dialog.init_framework_widget(
            self._discovery_plugin_definition
        )
        result.index = index
        result.set_asset_info(asset_info)
        result.change_asset_version.connect(self._on_change_asset_version)
        return result

    def _build_header(self, layout):
        '''Build the widget header, can be overridden in subclasses.'''
        row1 = QtWidgets.QWidget()
        row1.setLayout(QtWidgets.QHBoxLayout())
        row1.layout().setContentsMargins(5, 5, 5, 5)
        row1.layout().setSpacing(6)

        title = QtWidgets.QLabel('Tracked assets')
        title.setObjectName('h2')
        row1.layout().addWidget(title)

        row1.layout().addWidget(QtWidgets.QLabel(), 10)

        self._config_button = ApproveButton('ADD / REMOVE ASSETS')
        row1.layout().addWidget(self._config_button)

        layout.addWidget(row1)

        row2 = QtWidgets.QWidget()
        row2.setLayout(QtWidgets.QHBoxLayout())
        row2.layout().setContentsMargins(5, 5, 5, 5)
        row2.layout().setSpacing(6)

        self._search = SearchBox(collapsed=False, collapsable=False)
        row2.layout().addWidget(self._search)

        self._rebuild_button = CircularButton('sync')
        row2.layout().addWidget(self._rebuild_button)

        self._busy_widget = BusyIndicator(start=False)
        self._busy_widget.setMinimumSize(QtCore.QSize(24, 24))
        self._busy_widget.setVisible(False)
        row2.layout().addWidget(self._busy_widget)

        layout.addWidget(row2)

    def build(self):
        '''Build widgets and parent them.'''

        self._asset_list = ListSelector(
            self._asset_list_model, self._build_asset_widget
        )

        self._header = QtWidgets.QWidget()
        self._header.setLayout(QtWidgets.QVBoxLayout())
        self._header.layout().setContentsMargins(1, 1, 1, 10)
        self._header.layout().setSpacing(4)
        self._build_header(self._header.layout())
        self.layout().addWidget(self._header)

        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )
        self.layout().addWidget(self._scroll_area, 100)

        self._scroll_area.setWidget(self._asset_list)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self._rebuild_button.clicked.connect(self._on_rebuild)
        self._asset_list.rebuilt.connect(self._on_asset_list_refreshed)
        if self._config_button:
            self._config_button.clicked.connect(self._on_config)
        self._search.input_updated.connect(self._on_search)

    # Rebuild and Discovery

    def reset(self):
        self._asset_list_model.reset()

    def _on_asset_list_refreshed(self):
        pass

    def rebuild(self):
        '''Rebuild the asset list - (re-)discover DCC assets.'''
        self._rebuild_button.click()

    def setup_discovery(self, discovery_plugins):
        '''Setup discovery plugins from *discovery_plugins*.'''
        for plugin in discovery_plugins:
            self._discovery_plugin_definition = plugin
            return
        raise Exception('No discovery plugin found!')

    def _on_rebuild(self):
        '''Query DCC for scene assets by running the discover action.'''
        if not self._discovery_plugin_definition:
            raise Exception('No discovery plugin have been setup!')
        self._run_callback(self._discovery_plugin_definition)

    def set_asset_list(self, asset_entities_list):
        '''Clear model and add asset entities, will trigger list to be rebuilt.'''
        self._asset_list_model.reset()
        if asset_entities_list and 0 < len(asset_entities_list):
            self._asset_list.model.insertRows(0, asset_entities_list)

    # Actions

    def create_actions(self, actions):
        '''Dynamically register asset manager actions from definition *actions*.
        When an action is selected, the method identified with ui_callback action property
        will be called with the selected asset infos and the plugin as arguments.
        '''

        self._action_widgets = {}

        for action_type, actions in list(actions.items()):
            if action_type not in list(self._action_widgets.keys()):
                self._action_widgets[action_type] = []
            for action in actions:
                action_widget = QtWidgets.QAction(
                    action['name'],
                    self,
                )
                action_widget.setData(action)
                self._action_widgets[action_type].append(action_widget)

    def contextMenuEvent(self, event):
        '''(Override) Executes the context menu'''
        # Anything selected?
        widget_deselect = None
        if len(self._asset_list.selection()) == 0:
            # Select the clicked widget
            widget_select = self.childAt(event.x(), event.y())
            if widget_select:
                widget_select = widget_select.childAt(event.x(), event.y())
                if widget_select:
                    widget_select.setSelected(True)

        menu = QtWidgets.QMenu(self)
        self.action_type_menu = {}
        for action_type, action_widgets in list(self._action_widgets.items()):
            if action_type == 'remove' and not self.remove_enabled:
                continue  # Can only remove asset when in assembler
            if len(action_widgets) == 0:
                continue
            elif len(action_widgets) == 1:
                menu.addAction(action_widgets[0])
            else:
                if action_type not in list(self.action_type_menu.keys()):
                    type_menu = QtWidgets.QMenu(action_type.title(), self)
                    menu.addMenu(type_menu)
                    self.action_type_menu[action_type] = type_menu
                for action_widget in action_widgets:
                    self.action_type_menu[action_type].addAction(action_widget)
        menu.triggered.connect(self._context_menu_triggered)

        # add other required actions
        menu.exec_(QtGui.QCursor.pos())

    def _context_menu_triggered(self, action):
        '''
        Find and call the clicked function on the menu
        '''
        self._run_callback(action.data())

    def _run_callback(self, plugin):
        '''Run the plugin with the given *plugin* definition.'''
        ui_callback = plugin['ui_callback']
        if hasattr(self, ui_callback):
            callback_fn = getattr(self, ui_callback)
            callback_fn(self._asset_list.selection(), plugin)
        else:
            logger.warning(
                'Asset manager browser have no method for for ui_callback: {}!'.format(
                    ui_callback
                )
            )

    # Handle asset actions

    def _check_selection(self, selected_assets):
        '''Check if *selected_assets* is empty and show dialog message'''
        if len(selected_assets) == 0:
            ModalDialog(
                self,
                title='Error!',
                message="Please select at least one asset!",
            ).exec_()
            return False
        else:
            return True

    def _run_plugin(self, plugin_definition, callback, selected_assets=None):
        '''Emit run_plugin signal with *plugin_definition* and *callback*, providing
        *selected_assets* as data if given.'''
        # TODO: check why action arrive as dict and not expected DefinitionList object?
        plugin_config = (
            plugin_definition.to_dict()
            if not isinstance(plugin_definition, dict)
            else plugin_definition
        )

        method = 'run'
        if selected_assets:
            if len(selected_assets) > 1:
                method = 'run_multiple'
                plugin_config['data'] = selected_assets
            else:
                plugin_config['data'] = selected_assets[0]
        self.run_plugin.emit(plugin_config, method, callback)

    # Discover

    def ctx_discover(self, selected_assets, plugin_definition):
        self._run_plugin(plugin_definition, self._assets_discovered_callback)

    def _assets_discovered_callback(self, plugin_info):
        print(
            '@@@ _assets_discovered_callback: {}'.format(
                json.dumps(plugin_info, indent=2)
            )
        )
        asset_entities_list = []
        for ftrack_asset in plugin_info['plugin_method_result']:
            asset_entities_list.append(ftrack_asset)

        self.set_asset_list(asset_entities_list)

    # Select

    def ctx_select(self, selected_assets, plugin_definition):
        '''Select the *selected_assets* in the DCC by running plugin defined
        with *plugin_definition*.'''
        if not self._check_selection(selected_assets):
            return
        self._run_plugin(
            plugin_definition, self._assets_selected_callback, selected_assets
        )

    def _assets_selected_callback(self, plugin_info):
        print(
            '@@@ _assets_selected_callback: {}'.format(
                json.dumps(plugin_info, indent=2)
            )
        )

    # Update to latest

    # Change version

    def _on_change_asset_version(self, asset_info, version_entity):
        '''
        Triggered when a version of the asset has changed on the
        :obj:`version_cb_delegate`. Prompt user.
        '''
        self.change_asset_version.emit(asset_info.copy(), version_entity['id'])

    # Unload

    # Load

    def _on_config(self):
        '''Callback when user wants to open the assembler'''
        self.on_config.emit()

    def _on_search(self, text):
        '''Filter asset list, only show assets matching *text*.'''
        self._asset_list.refresh(text)


class AssetAssemblerBrowser(AssetManagerBrowser):
    '''A specialized asset manager browser intended to be docked within the
    assembler during load, and enables remove assets from the DCC.'''

    remove_enabled = True  # Enable remove of assets

    def _build_header(self, layout):
        '''(Override) Build assembler docked header and add to *layout*'''
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

        self._search = SearchBox(collapsed=True, collapsable=True)
        row2.layout().addWidget(self._search)

        self._rebuild_button = CircularButton('sync')
        row2.layout().addWidget(self._rebuild_button)

        self._busy_widget = BusyIndicator(start=False)
        self._busy_widget.setMinimumSize(QtCore.QSize(16, 16))
        row2.layout().addWidget(self._busy_widget)
        self._busy_widget.setVisible(False)

        layout.addWidget(row2)
