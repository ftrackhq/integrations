# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import json

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_widget.widget import FrameworkWidget

from ftrack_constants.framework import asset as asset_const

from ftrack_utils.string import str_version

from ftrack_qt.utils.widget import clear_layout
from ftrack_qt.widgets.accordion import AccordionWidget
from ftrack_qt.widgets.headers import AssetAccordionHeaderWidget
from ftrack_qt.widgets.thumbnails import (
    AssetVersion as AssetVersionThumbnail,
)
from ftrack_qt.widgets.info import EntityInfo, ComponentAndVersionWidget
from ftrack_qt.widgets.lines import LineWidget
from ftrack_qt.widgets.dialogs import ModalDialog


class GenericAssetItem(FrameworkWidget, AccordionWidget):
    '''Accordion widget tailored for presenting an asset (component entity),
    driven by DCC compatible asset_info data type.'''

    name = 'generic_asset_item'
    ui_type = 'qt'

    change_asset_version = QtCore.Signal(object, object)  # User change version

    @property
    def options_widget(self):
        '''Return the widget representing options'''
        return self._options_button

    @property
    def session(self):
        return self._event_manager.session

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_definition,
        dialog_connect_methods_callback,
        dialog_property_getter_connection_callback,
        parent=None,
    ):
        '''
        Initialize asset item widget

        :param index: The index this asset has in list
        :param parent: The parent dialog or frame
        '''
        self._version_id = None
        AccordionWidget.__init__(
            self,
            selectable=True,
            show_checkbox=False,
            checked=False,
            parent=parent,
        )
        FrameworkWidget.__init__(
            self,
            event_manager,
            client_id,
            context_id,
            plugin_definition,
            dialog_connect_methods_callback,
            dialog_property_getter_connection_callback,
            parent=parent,
        )

    def build_header(self):
        '''(Override) Provide an extended header with options and status icon'''
        return AssetAccordionHeaderWidget(
            title=self.title,
            checkable=self.checkable,
            checked=self.checked,
            show_checkbox=self.show_checkbox,
            collapsable=self.collapsable,
            collapsed=self.collapsed,
        )

    def build(self):
        '''(Override) Initialize the accordion content'''
        super(GenericAssetItem, self).build()
        self.content_widget.layout().setContentsMargins(10, 2, 10, 2)
        self.content_widget.layout().setSpacing(5)

    def set_asset_info(self, asset_info):
        '''Update widget from asset data provided in *asset_info*'''
        self._version_id = asset_info[asset_const.VERSION_ID]
        version = self.session.query(
            'select is_latest_version from AssetVersion where id={}'.format(
                self._version_id
            )
        ).one()
        # Calculate path
        parent_path = ''
        if version['task'] and version['task']['link']:
            parent_path = [link['name'] for link in version['task']['link']]
        self.header_widget.path_widget.setText(' / '.join(parent_path))
        self.header_widget.asset_name_widget.setText(
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
        self.header_widget.status_widget.set_status(version['status'])
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
        self.header_widget.component_and_version_widget.set_component_filename(
            self._component_path
        )
        self.header_widget.component_and_version_widget.set_version(
            asset_info[asset_const.VERSION_NUMBER]
        )
        self.header_widget.component_and_version_widget.set_latest_version(
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
        if (
            self.header_widget.path_widget.text().lower().find(search_text)
            > -1
        ):
            return True
        if (
            self.header_widget.asset_name_widget.text()
            .lower()
            .find(search_text)
            > -1
        ):
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

    def _on_collapse(self, collapsed):
        '''(Override) Dynamically populate asset expanded view'''
        # Remove all content widgets
        clear_layout(self.content_widget.layout())
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

            self.content_widget.layout().addStretch()

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
