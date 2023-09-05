# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json
import logging

from Qt import QtWidgets, QtCore, QtGui

from ftrack_constants.framework import asset as asset_const

from ftrack_utils.string import str_version

from ftrack_qt.widgets.dialogs import ModalDialog
from ftrack_qt.widgets.search import SearchBox
from ftrack_qt.widgets.selectors import ListSelector
from ftrack_qt.widgets.accordion import AccordionWidget
from ftrack_qt.widgets.buttons import ApproveButton, CircularButton
from ftrack_qt.widgets.overlay import BusyIndicator
from ftrack_qt.widgets.thumbnails import (
    AssetVersion as AssetVersionThumbnail,
)
from ftrack_qt.widgets.info import EntityInfo
from ftrack_qt.widgets.lines import LineWidget

logger = logging.getLogger(__name__)


class AssetManagerBrowser(QtWidgets.QWidget):
    '''Widget for browsing amd modifying assets loaded within a DCC'''

    # Signals
    refresh = QtCore.Signal()  # Asset list has been refreshed
    change_asset_version = QtCore.Signal(
        object, object
    )  # User has requested a change of asset version
    on_config = QtCore.Signal()  # User has requested to configure assets
    stop_busy_indicator = QtCore.Signal()  # Stop spinner and hide it

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def __init__(
        self, in_assembler, event_manager, asset_list_model, parent=None
    ):
        super(AssetManagerBrowser, self).__init__(parent=parent)
        self._event_manager = event_manager
        self._asset_list_model = asset_list_model
        self._in_assembler = in_assembler

        self._callback_handler = None
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

        self._asset_list = ListSelector(
            self._asset_list_model, self._build_asset_widget
        )

    def _build_asset_widget(self, index, asset_info):
        '''Factory creating an asset widget for *index* and *asset_info*.'''
        result = AssetWidget(index)
        result.set_asset_info(asset_info)
        result.change_asset_version.connect(self._on_change_asset_version)
        return result

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
        row1.layout().addWidget(self._config_button)

        layout.addWidget(row1)

        row2 = QtWidgets.QWidget()
        row2.setLayout(QtWidgets.QHBoxLayout())
        row2.layout().setContentsMargins(5, 5, 5, 5)
        row2.layout().setSpacing(6)

        row2.layout().addWidget(self._build_search_widget())

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

        row2.layout().addWidget(self._build_search_widget())

        self._rebuild_button = CircularButton('sync')
        row2.layout().addWidget(self._rebuild_button)

        self._busy_widget = BusyIndicator(start=False)
        self._busy_widget.setMinimumSize(QtCore.QSize(16, 16))
        row2.layout().addWidget(self._busy_widget)
        self._busy_widget.setVisible(False)

        layout.addWidget(row2)

    def _build_header(self, layout):
        '''(Override)'''
        self._build_docked_header(
            layout
        ) if not self._in_assembler else self._build_assembler_header(layout)

    def _build_search_widget(self):
        '''Create search input'''
        self._search = SearchBox(
            collapsed=self._in_assembler, collapsable=self._in_assembler
        )
        return self._search

    def build(self):
        '''Build widgets and parent them.'''
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

    def _on_asset_list_refreshed(self):
        pass

    def _on_config(self):
        '''Callback when user wants to open the assembler'''
        self.on_config.emit()

    def rebuild(self):
        '''Rebuild the asset list - (re-)discover DCC assets.'''
        self._rebuild_button.click()

    def _on_rebuild(self):
        '''Query DCC for scene assets by running the discover action.'''
        for action_type, action_widgets in list(self._action_widgets.items()):
            if action_type == 'discover':
                for action_widget in action_widgets:
                    self._context_menu_triggered(action_widget)
                    # action_widget.trigger()
                    return
                break
        logger.warning('No discover action found for asset manager!')

    def create_actions(self, actions, callback_handler):
        '''Dynamically register asset manager actions from definition *actions*, when
        selected *callback_handler*, the method identified with ui_callback action property
        will be called with the selected asset infos and the plugin as arguments.
        '''

        self._callback_handler = callback_handler

        self._action_widgets = {}

        for action_type, actions in list(actions.items()):
            if action_type not in list(self._action_widgets.keys()):
                self._action_widgets[action_type] = []
            for action in actions:
                action_widget = QtWidgets.QAction(
                    action['label']
                    if len(action['label'] or '') > 0
                    else action['name'],
                    self,
                )
                action_widget.setData(action)
                self._action_widgets[action_type].append(action_widget)

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

        menu = QtWidgets.QMenu(self)
        self.action_type_menu = {}
        for action_type, action_widgets in list(self._action_widgets.items()):
            if not self._in_assembler and action_type == 'remove':
                continue  # Can only remove asset when in assembler
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
        plugin = action.data()
        # plugin['name'].replace(' ', '_')
        ui_callback = plugin['ui_callback']
        if hasattr(self._callback_handler, ui_callback):
            callback_fn = getattr(self._callback_handler, ui_callback)
            callback_fn(self._asset_list.selection(), plugin)
        else:
            logger.warning(
                'Callback handler have no method for for ui_callback: {}!'.format(
                    ui_callback
                )
            )

    def _on_change_asset_version(self, asset_info, version_entity):
        '''
        Triggered when a version of the asset has changed on the
        :obj:`version_cb_delegate`. Prompt user.
        '''
        self.change_asset_version.emit(asset_info.copy(), version_entity['id'])

    def set_asset_list(self, asset_entities_list):
        '''Clear model and add asset entities, will trigger list to be rebuilt.'''
        self._asset_list_model.reset()
        if asset_entities_list and 0 < len(asset_entities_list):
            self._asset_list.model.insertRows(0, asset_entities_list)

    def _on_search(self, text):
        '''Filter asset list, only show assets matching *text*.'''
        self._asset_list.refresh(text)


class AssetWidget(AccordionWidget):
    '''Minimal widget representation of an asset(asset_info)'''

    change_asset_version = QtCore.Signal(object, object)  # User change version

    @property
    def options_widget(self):
        '''Return the widget representing options'''
        return self._options_button

    def __init__(self, index, parent=None):
        '''
        Initialize asset widget

        :param index: The index this asset has in list
        :param event_manager:  :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param docked: Boolean telling if the list is docked in DCC or is within an ftrack dialog - drive style
        :param parent: The parent dialog or frame
        '''
        super(AssetWidget, self).__init__(
            AccordionWidget.SELECT_MODE_LIST,
            AccordionWidget.CHECK_MODE_NONE,
            checked=False,
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
        self._version_id = asset_info[asset_const.VERSION_ID]
        version = self.session.query(
            'select is_latest_version from AssetVersion where id={}'.format(
                self._version_id
            )
        ).one()
        # Calculate path
        parent_path = [link['name'] for link in version['task']['link']]
        self._path_widget.setText(' / '.join(parent_path))
        self._asset_name_widget.setText(
            '{} '.format(asset_info[asset_const.ASSET_NAME])
        )

        query = (
            'select is_latest_version, id, asset, components, components.name, '
            'components.id, version, asset , asset.name, asset.type.name from '
            'AssetVersion where asset.id is "{}" and components.name is "{}"'
            'order by version ascending'
        ).format(
            asset_info[asset_const.ASSET_ID],
            asset_info[asset_const.COMPONENT_NAME],
        )
        versions = self.session.query(query).all()

        self._versions_collection = versions
        self._version_nr = version['version']
        self._status_widget.set_status(version['status'])
        self._load_mode = asset_info[asset_const.LOAD_MODE]

        indicator_color = 'gray'
        self._is_loaded = asset_info.get(asset_const.OBJECTS_LOADED)
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
        self._component_path = asset_info[asset_const.COMPONENT_NAME] or '?.?'
        self._component_and_version_header_widget.set_component_filename(
            self._component_path
        )
        self._component_and_version_header_widget.set_version(
            asset_info[asset_const.VERSION_NUMBER]
        )
        self._component_and_version_header_widget.set_latest_version(
            self._is_latest_version
        )
        self._load_mode = asset_info[asset_const.LOAD_MODE]
        self._asset_info_options = asset_info[asset_const.ASSET_INFO_OPTIONS]
        # Info
        self._published_by = version['user']
        self._published_date = version['date']
        # Deps
        self._version_dependency_ids = asset_info[asset_const.DEPENDENCY_IDS]

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
                self.add_widget(LineWidget())

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

                self.add_widget(LineWidget())

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
                self.change_asset_version.emit(self.index, version)
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
