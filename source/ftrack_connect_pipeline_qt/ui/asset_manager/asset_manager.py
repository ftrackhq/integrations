# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from functools import partial
import six
import base64
import json

from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.constants import asset as asset_constants
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
from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import (
    MaterialIconWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    AssetVersion as AssetVersionThumbnail,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo
from ftrack_connect_pipeline_qt.ui.utility.widget import line
from ftrack_connect_pipeline_qt.utils import clear_layout


class AssetManagerWidget(AssetManagerBaseWidget):
    '''Base widget of the asset manager and is_assembler'''

    refresh = QtCore.Signal()
    rebuild = QtCore.Signal()

    widget_status_updated = QtCore.Signal(object)
    change_asset_version = QtCore.Signal(object, object)
    select_assets = QtCore.Signal(object)
    remove_assets = QtCore.Signal(object)
    update_assets = QtCore.Signal(object, object)
    load_assets = QtCore.Signal(object)
    unload_assets = QtCore.Signal(object)

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
        return self._host_connection

    @host_connection.setter
    def host_connection(self, host_connection):
        '''Sets :obj:`host_connection` with the given *host_connection*.'''
        self._host_connection = host_connection
        # self._listen_widget_updates()

    def __init__(
        self, is_assembler, event_manager, asset_list_model, parent=None
    ):
        super(AssetManagerWidget, self).__init__(
            is_assembler, event_manager, asset_list_model, parent=parent
        )
        self._host_connection = None

    def init_header_content(self, layout):
        '''Create toolbar'''
        title = QtWidgets.QLabel('Tracked assets')
        title.setObjectName('h2')
        layout.addWidget(title)
        layout.addWidget(self.init_search())
        self._refresh_button = CircularButton('sync', '#87E1EB')
        self._refresh_button.clicked.connect(self._on_rebuild)
        layout.addWidget(self._refresh_button)
        if not self._is_assembler:
            self._config_button = CircularButton('cog', '#87E1EB')
            self._config_button.clicked.connect(self._on_config)
            layout.addWidget(self._config_button)
        else:
            self._add_button = CircularButton('plus', '#87E1EB')
            self._add_button.clicked.connect(self._on_add)
            layout.addWidget(self._add_button)

    def build(self):
        super(AssetManagerWidget, self).build()

        self._asset_list = AssetManagerListWidget(
            self._asset_list_model, AssetWidget
        )

        asset_list_container = QtWidgets.QWidget()
        asset_list_container.setLayout(QtWidgets.QVBoxLayout())
        asset_list_container.layout().setContentsMargins(0, 0, 0, 0)
        asset_list_container.layout().setSpacing(0)
        asset_list_container.layout().addWidget(self._asset_list)
        asset_list_container.layout().addWidget(QtWidgets.QLabel(''), 1000)

        self.scroll.setWidget(asset_list_container)

    def post_build(self):
        super(AssetManagerWidget, self).post_build()
        self.refresh.connect(self._on_refresh)

    def set_asset_list(self, asset_entities_list):
        '''Clear model and add asset entities, will trigger list to be rebuilt.'''
        self._asset_list_model.reset()
        if asset_entities_list and 0 < len(asset_entities_list):
            self._asset_list.model.insertRows(0, asset_entities_list)

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
        if len(self._asset_list.selection(warn_on_empty=False)) == 0:
            # Temporaily select the clicked widget
            widget_deselect = self.childAt(event.x(), event.y())
            if widget_deselect:
                widget_deselect = widget_deselect.childAt(event.x(), event.y())
                if widget_deselect:
                    widget_deselect.header.checkbox.setChecked(True)

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

    def ctx_update(self, plugin):
        '''
        Triggered when update action menu been clicked.
        Emits update_asset signal.
        Uses the given *plugin* to update the selected assets
        '''
        self.update_assets.emit(
            self._asset_list.selection(warn_on_empty=True), plugin
        )

    def ctx_select(self, plugin):
        '''
        Triggered when select action menu been clicked.
        Emits select_asset signal.
        '''
        self.select_assets.emit(self._asset_list.selection(warn_on_empty=True))

    def ctx_remove(self, plugin):
        '''
        Triggered when remove action menu been clicked.
        Emits remove_asset signal.
        '''
        self.remove_assets.emit(self._asset_list.selection(warn_on_empty=True))

    def ctx_load(self, plugin):
        # TODO: I think is better to not pass a Plugin, and use directly the
        # function in the engine. But if we want, we can pass the plugin here,
        # to for example define a standard load plugin or a check plugin to
        # execute after the load plugin that is
        # saved in the asset info is executed.
        '''
        Triggered when load action menu been clicked.
        Emits load_assets signal to load the selected assets in the scene.
        '''
        self.load_assets.emit(self._asset_list.selection(warn_on_empty=True))

    def ctx_unload(self, plugin):
        '''
        Triggered when unload action menu been clicked.
        Emits load_assets signal to unload the selected assets in the scene.
        '''
        self.unload_assets.emit(self._asset_list.selection(warn_on_empty=True))

    def set_context_actions(self, actions):
        '''Set the :obj:`engine_type` into the asset_table_view and calls the
        create_action function of the same class with the given *actions* from
        definition'''
        self.engine_type = self.engine_type
        self.create_actions(actions)

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        # Check if this is a asset discover notification
        print('@@@ _update_widget({})'.format(event))
        if event['data']['pipeline'].get('method') == 'discover_assets':
            # This could be executed async, rebuild asset list through signal
            self.rebuild.emit()

    def _listen_widget_updates(self):
        '''Subscribe to the PIPELINE_CLIENT_NOTIFICATION topic to call the
        _update_widget function when the host returns and answer through the
        same topic'''

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                core_constants.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id,
            ),
            self._update_widget,
        )

    def _on_refresh(self):
        '''Refresh the asset list from the model data.'''
        self._asset_list.rebuild()

    def _on_rebuild(self):
        '''Query DCC for scene assets.'''
        self.rebuild.emit()  # To be picked up by AM

    def _on_config(self):
        raise NotImplementedError('Open Assembler not implemented yet!')

    def _on_add(self):
        raise NotImplementedError('Open Importer not implemented yet!')

    def on_asset_change_version(self, index, value):
        '''
        Triggered when a version of the asset has changed on the
        :obj:`version_cb_delegate`
        '''
        _asset_info = self._asset_list.model.getData(index.row())
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


class AssetManagerListWidget(AssetListWidget):
    '''Custom asset manager list view'''

    def __init__(self, model, asset_widget_class, parent=None):
        self._asset_widget_class = asset_widget_class
        super(AssetManagerListWidget, self).__init__(model, parent=parent)

    def post_build(self):
        super(AssetManagerListWidget, self).post_build()
        # Do not distinguish between different model events,
        # always rebuild entire list from scratch for now.
        self._model.rowsInserted.connect(self._on_asset_data_changed)
        self._model.modelReset.connect(self._on_asset_data_changed)
        self._model.rowsRemoved.connect(self._on_asset_data_changed)
        self._model.dataChanged.connect(self._on_asset_data_changed)

    def _on_asset_data_changed(self, *args):
        self.rebuild()
        self.selection_updated.emit(self.selection())

    def rebuild(
        self,
    ):
        '''Clear widget and add all assets again from model.'''
        print('@@@ AssetManagerListWidget::rebuilt()')
        clear_layout(self.layout())
        # TODO: Save selection state
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)
            asset_info = self.model.data(index)
            asset_widget = self._asset_widget_class(
                index, self.model.event_manager
            )
            asset_widget.set_asset_info(asset_info)
            self.layout().addWidget(asset_widget)
            asset_widget.clicked.connect(
                partial(self.asset_clicked, asset_widget)
            )


class AssetWidget(AccordionBaseWidget):
    '''Widget representation of a minimal asset representation'''

    @property
    def index(self):
        return self._index

    @property
    def options_widget(self):
        return self._options_button

    def __init__(self, index, event_manager, title=None, parent=None):
        super(AssetWidget, self).__init__(
            AccordionBaseWidget.SELECT_MODE_LIST,
            AccordionBaseWidget.CHECK_MODE_NONE,
            event_manager=event_manager,
            title=title,
            checked=False,
            parent=parent,
        )
        self._version_id = None
        self._index = index

    def init_status_widget(self):
        self._status_widget = AssetVersionStatusWidget()
        # self._status_widget.setObjectName('borderless')
        return self._status_widget

    def init_header_content(self, header_layout, collapsed):
        '''Add publish related widgets to the accordion header'''
        header_layout.setContentsMargins(1, 1, 1, 1)
        header_layout.setSpacing(2)
        self._asset_name_widget = QtWidgets.QLabel()
        self._asset_name_widget.setObjectName('h4')
        header_layout.addWidget(self._asset_name_widget)
        self._component_and_version_header_widget = ComponentAndVersionWidget(
            True
        )
        header_layout.addWidget(self._component_and_version_header_widget)
        header_layout.addStretch()
        header_layout.addWidget(self.init_status_widget())

    def init_content(self, content_layout):
        # self.content.setMinimumHeight(200)
        content_layout.setContentsMargins(10, 2, 10, 2)
        content_layout.setSpacing(5)

    def set_asset_info(self, asset_info):
        '''Update widget from data'''
        self._version_id = asset_info[asset_constants.VERSION_ID]
        self._asset_name_widget.setText(
            '{} '.format(asset_info[asset_constants.ASSET_NAME])
        )
        self._versions_collection = asset_info[
            asset_constants.ASSET_VERSIONS_ENTITIES
        ]
        version = self.session.query(
            'AssetVersion where id={}'.format(self._version_id)
        ).one()
        self._status_widget.set_status(version['status'])
        self._load_mode = asset_info[asset_constants.LOAD_MODE]

        self.set_indicator(
            asset_info.get(asset_constants.IS_LOADED) in [True, 'True']
        )
        self._component_path = (
            asset_info[asset_constants.COMPONENT_NAME] or '?.?'
        )
        self._component_and_version_header_widget.set_component_filename(
            self._component_path
        )
        self._component_and_version_header_widget.set_version(
            asset_info[asset_constants.VERSION_NUMBER]
        )
        self._is_latest_version = asset_info[asset_constants.IS_LATEST_VERSION]
        self._component_and_version_header_widget.set_latest_version(
            self._is_latest_version
        )
        self._load_mode = asset_info[asset_constants.LOAD_MODE]
        self._version_dependency_ids = asset_info[
            asset_constants.DEPENDENCY_IDS
        ]
        self._asset_info_options = asset_info[
            asset_constants.ASSET_INFO_OPTIONS
        ]

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
                self._thumbnail_widget.setMinimumSize(69, 48)
                self._thumbnail_widget.setMaximumSize(69, 48)
                context_widget.layout().addWidget(self._thumbnail_widget)

                self._component_and_version_widget = ComponentAndVersionWidget(
                    False
                )
                self._component_and_version_widget.set_component_filename(
                    self._component_path
                )

                self._component_and_version_widget.version_selector.clear()
                for asset_version in self._versions_collection:
                    self._component_and_version_widget.version_selector.addItem(
                        'v{}'.format(asset_version['version']),
                        asset_version['id'],
                    )
                self._component_and_version_widget.set_latest_version(
                    self._is_latest_version
                )

                # Add context info with version selection
                self._entity_info = EntityInfo(
                    additional_widget=self._component_and_version_widget
                )
                self._entity_info.set_entity(version['asset']['parent'])
                self._entity_info.setMinimumHeight(100)
                context_widget.layout().addWidget(self._entity_info, 100)
                # context_widget.layout().addWidget(QtWidgets.QLabel('Test'))

            self.add_widget(context_widget)

            self.add_widget(line.Line())

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

            if 0 < len(self._version_dependency_ids or []):
                self.add_widget(line.Line())

                dependencies_label = QtWidgets.QLabel('DEPENDENCIES:')
                dependencies_label.setObjectName('h4')
                self.add_widget(dependencies_label)

                for dep_version_id in self._version_dependency_ids or []:
                    dep_version = self.session.query(
                        'AssetVersion where id={}'.format(dep_version_id)
                    ).first()

                    if dep_version:
                        dep_version_widget = QtWidgets.QWidget()
                        dep_version_widget.setLayout(QtWidgets.QHBoxLayout())
                        dep_version_widget.setContentsMargins(15, 1, 1, 1)
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
                        dep_entity_info = EntityInfo()
                        dep_entity_info.set_entity(version['asset']['parent'])
                        dep_entity_info.setMinimumHeight(100)
                        context_widget.layout().addWidget(dep_entity_info, 100)

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

    def update_input(self, message, status):
        '''Update the accordion input summary, should be overridden by child.'''
        pass


class AssetVersionSelector(QtWidgets.QComboBox):
    def __init__(self):
        super(AssetVersionSelector, self).__init__()


class AssetVersionStatusWidget(QtWidgets.QFrame):
    def __init__(self):
        super(AssetVersionStatusWidget, self).__init__()

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
        self.setStyleSheet(
            '''
            QFrame {
                border: 1px solid %s;
            }
         '''
            % (status['color'])
        )


class ComponentAndVersionWidget(QtWidgets.QWidget):
    @property
    def version_selector(self):
        return self._version_selector

    def __init__(self, collapsed, parent=None):
        super(ComponentAndVersionWidget, self).__init__(parent=parent)

        self._collapsed = collapsed

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        self._component_filename_widget = QtWidgets.QLabel()
        self._component_filename_widget.setObjectName('gray')
        self.layout().addWidget(self._component_filename_widget)
        self.layout().addWidget(QtWidgets.QLabel(' - '))

        if self._collapsed:
            self._version_nr_widget = QtWidgets.QLabel()
            self.layout().addWidget(self._version_nr_widget)
        else:
            self._version_selector = AssetVersionSelector()
            self._version_selector.setMaximumHeight(20)
            self.layout().addWidget(self._version_selector)

    def post_build(self):
        pass

    def set_latest_version(self, is_latest_version):
        color = '#935BA2' if is_latest_version else '#FFBA5C'
        if self._collapsed:
            self._version_nr_widget.setStyleSheet('color: {}'.format(color))
        else:
            self._version_selector.setStyleSheet(
                '''
                color: {0};
                border: 1px solid {0};
            '''.format(
                    color
                )
            )

    def set_component_filename(self, component_path):
        self._component_filename_widget.setText(
            '({})'.format(component_path.replace('\\', '/').split('/')[-1])
        )

    def set_version(self, version_nr):
        if self._collapsed:
            self._version_nr_widget.setText('v{}'.format(str(version_nr)))
