# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_constants.framework import status
from ftrack_constants.framework import asset as asset_const
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

    run_plugin = QtCore.Signal(object, object)
    # Run plugin with *plugin_configuration* and *plugin_method_name*.

    run_action = QtCore.Signal(object)
    # Run action(step) with action *context_data*

    client_notify_ui_run_plugin_progress = QtCore.Signal(object)
    # Plugin run progress has been updated with *plugin_info* provided

    client_notify_ui_run_plugin_result = QtCore.Signal(object)
    # Plugin run result has been updated with *plugin_info* provided

    client_notify_ui_run_action_result = QtCore.Signal(object, object)
    # Definition run result has been updated with *action_type* and *definition_result* provided

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

    @property
    def busy(self):
        '''Returns true if the browser is in busy mode'''
        return self._busy_widget.isVisible()

    @busy.setter
    def busy(self, value):
        '''Enter busy mode if *value* is True - start spinner and show it.
        If *value* is false, stop and hide the spinner'''
        if value:
            self._busy_widget.start()
            self._rebuild_button.setVisible(False)
            self._busy_widget.setVisible(True)
        else:
            self._busy_widget.stop()
            self._busy_widget.setVisible(False)
            self._rebuild_button.setVisible(True)

    @property
    def error_message(self):
        '''Return the most recent error message provided by plugin run progress'''
        return self._error_message

    @error_message.setter
    def error_message(self, value):
        '''Set the most recent error message provided by plugin run progress'''
        self._error_message = value

    def __init__(self, framework_dialog, parent=None):
        '''Instantiate the browser within parent *framework_dialog*'''
        super(AssetManagerBrowser, self).__init__(parent=parent)
        self._framework_dialog = framework_dialog
        self._asset_list_model = AssetInfoListModel()
        self._discovery_plugin_definition = None
        self._error_message = None

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
        self.client_notify_ui_run_plugin_progress.connect(
            self._on_client_notify_ui_run_plugin_progress
        )
        self.client_notify_ui_run_plugin_result.connect(
            self._on_client_notify_ui_run_plugin_result
        )
        self.client_notify_ui_run_action_result.connect(
            self._on_client_notify_ui_run_action_result
        )

    # Rebuild and Discovery

    def reset(self):
        self._asset_list_model.reset()

    def _on_asset_list_refreshed(self):
        pass

    def rebuild(self):
        '''Rebuild the asset list - (re-)discover DCC assets.'''
        self._rebuild_button.click()

    def setup_discovery(self, discovery_plugins):
        '''Setup discovery plugins from *discovery_plugins*, consider only one plugin for now.'''
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
        will be called with the selected asset infos and the step configuration as arguments.
        '''

        self._action_widgets = {}
        self._change_version_action = None

        for action in actions:
            action_type = action['type']
            if len(action['ui_callback'] or '') == 0:
                self._change_version_action = action
                continue  # Do not have change version action in the menu
            if action_type not in list(self._action_widgets.keys()):
                self._action_widgets[action_type] = []
            action_widget = QtWidgets.QAction(
                action['name'],
                self,
            )
            action_widget.setData(action)
            self._action_widgets[action_type].append(action_widget)

    def contextMenuEvent(self, event):
        '''(Override) Executes the context menu, if not busy'''
        if self.busy:
            return
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
            if action_type == 'remove' and not self.remove_enabled and False:
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

    def _run_callback(self, configuration):
        '''Run the plugin with the given *step_configuration* definition.'''
        ui_callback = configuration['ui_callback']
        if hasattr(self, ui_callback):
            callback_fn = getattr(self, ui_callback)
            callback_fn(self._asset_list.selection(), configuration)
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

    def _run_plugin(self, plugin_definition):
        '''Emit run_plugin signal with *plugin_definition*, providing
        *selected_assets* as data if given.'''
        # TODO: check why action arrive as dict and not expected DefinitionList object?
        plugin_config = (
            plugin_definition.to_dict()
            if not isinstance(plugin_definition, dict)
            else plugin_definition
        )
        self.error_message = None
        self.run_plugin.emit(plugin_config, 'run')

    def _run_action(self, context_data):
        '''Emit run_action signal providing *context_data* if given.'''
        self.busy = True
        self.error_message = None
        self.run_action.emit(context_data)

    def _on_client_notify_ui_run_plugin_progress(self, plugin_info):
        '''Handle progress notification from running plugin.'''
        plugin_status = plugin_info['plugin_status']
        if plugin_status in [status.ERROR_STATUS, status.EXCEPTION_STATUS]:
            self.busy = False
            # Store plugin error message
            plugin_method_result = plugin_info['plugin_method_result']
            if (
                isinstance(plugin_method_result, tuple)
                and len(plugin_method_result) == 2
                and isinstance(plugin_method_result[1], dict)
                and 'message' in plugin_method_result[1]
            ):
                self.error_message = plugin_method_result[1]['message']
            elif 'plugin_message' in plugin_info:
                self.error_message = plugin_info['plugin_message']
            if plugin_info['plugin_type'] != 'action':
                # Show error message
                ModalDialog(
                    self,
                    title='{} failed!'.format(
                        plugin_info['plugin_type'].title()
                    ),
                    message=self.error_message
                    + "\n\nPlease check the log viewer / "
                    "file logs for more details.",
                ).exec_()
        elif (
            plugin_status == status.SUCCESS_STATUS
            and plugin_info['plugin_type'] == 'action'
        ):
            # Updated asset info arrives from executing plugin(s) within action, update asset list model
            result = plugin_info['plugin_method_result']
            if isinstance(result, list):
                # Multiple assets - result from discovery
                asset_entities_list = result
                self.set_asset_list(asset_entities_list)
            elif isinstance(result, dict):
                # Single assets - result from asset add or modification
                asset_info = result
                index = self._asset_list_model.getIndex(
                    asset_info[asset_const.ASSET_INFO_ID]
                )
                if index:
                    self._asset_list_model.setData(index, asset_info)
                else:
                    # Not found, add to model
                    # TODO: Support remove of assets
                    self._asset_list_model.insertRows(
                        self._asset_list_model.rowCount(), asset_info
                    )
            elif isinstance(result, bool):
                # Remove asset
                asset_info = plugin_info['plugin_context_data']['asset_info']
                index = self._asset_list_model.getIndex(
                    asset_info[asset_const.ASSET_INFO_ID]
                )
                if index:
                    self._asset_list_model.removeRows(index, 1)

    def _on_client_notify_ui_run_plugin_result(self, plugin_info):
        '''Handle result notification from running plugin.'''
        plugin_status = plugin_info['plugin_status']
        self.busy = False
        if plugin_status == status.SUCCESS_STATUS:
            # Updated asset infos arrives from single plugin run, update asset list model
            result = plugin_info['plugin_method_result']
            if isinstance(result, list):
                # Multiple assets - result from discovery
                asset_entities_list = result
                self.set_asset_list(asset_entities_list)

    def _on_client_notify_ui_run_action_result(
        self, action_type, action_result
    ):
        '''Handle result notification from definition/action run.'''
        self.busy = False
        error_message = None
        if action_result != status.SUCCESS_STATUS:
            error_message = self.error_message
            if not error_message:
                # Provide a generic error message based on action performed
                if action_type == 'select':
                    error_message = 'Could not select asset(s)!'
                elif action_type == 'update':
                    error_message = (
                        'Could not update asset(s) to latest version!'
                    )
        if error_message:
            ModalDialog(self, message=error_message).exec_()

    # Discover

    def ctx_discover(self, selected_assets, plugin_definition):
        '''Discover *selected_assets* in the DCC by action, result will be returned through
        plugin result notify event.'''
        self.busy = True
        self._run_plugin(plugin_definition)

    # Select

    def ctx_select(self, selected_assets, action_configuration):
        '''Select the *selected_assets* in the DCC by action
        defined with *action_configuration*.'''
        if not self._check_selection(selected_assets):
            return
        context_data = {
            "action": action_configuration['type'],
            "assets": selected_assets,
        }
        self._run_action(context_data)

    # Update to latest

    def ctx_update(self, selected_assets, action_configuration):
        '''Update *selected_assets* in the DCC to latest version by action
        defined with *action_configuration*.'''
        if not self._check_selection(selected_assets):
            return
        context_data = {
            "action": action_configuration['type'],
            "assets": selected_assets,
        }
        self._run_action(context_data)

    # Change version

    def _on_change_asset_version(self, asset_info, version_entity):
        '''
        Triggered when a version of the asset has changed on the
        :obj:`version_cb_delegate`. Change version.
        '''
        context_data = {
            'action': self._change_version_action['type'],
            'assets': [asset_info],
            'new_version_id': version_entity['id'],
        }
        self._run_action(context_data)

    # Unload

    def ctx_unload(self, selected_assets, action_configuration):
        '''Unload *selected_assets* in the DCC to latest version by action
        defined with *action_configuration*.'''
        if not self._check_selection(selected_assets):
            return
        context_data = {
            "action": action_configuration['type'],
            "assets": selected_assets,
        }
        self._run_action(context_data)

    # Load

    def ctx_load(self, selected_assets, action_configuration):
        '''Unload *selected_assets* in the DCC to latest version by action
        defined with *action_configuration*.'''
        if not self._check_selection(selected_assets):
            return
        context_data = {
            "action": action_configuration['type'],
            "assets": selected_assets,
        }
        self._run_action(context_data)

    # Remove

    def ctx_remove(self, selected_assets, action_configuration):
        '''Remove *selected_assets* in the DCC to latest version by action
        defined with *action_configuration*.'''
        if not self._check_selection(selected_assets):
            return
        context_data = {
            "action": action_configuration['type'],
            "assets": selected_assets,
        }
        self._run_action(context_data)

    # Misc

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
