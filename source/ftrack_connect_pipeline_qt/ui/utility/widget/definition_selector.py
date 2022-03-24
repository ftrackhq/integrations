import logging
import json
import copy
from functools import partial

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt import constants as qt_constants


class DefinitionItem(QtWidgets.QPushButton):
    @property
    def definition(self):
        return self._definition

    @property
    def component_names_filter(self):
        return self._component_names_filter

    def __init__(
        self, text, definition_item, component_names_filter, parent=None
    ):
        super(DefinitionItem, self).__init__(text, parent=parent)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self._definition = definition_item
        self._component_names_filter = component_names_filter
        self.setMinimumWidth(80)


class DefinitionSelectorWidgetBase(QtWidgets.QWidget):
    '''DefinitionSelector Base Class'''

    hostsDiscovered = QtCore.Signal(object)
    hostChanged = QtCore.Signal(object)
    definitionChanged = QtCore.Signal(object, object, object)
    refreshed = QtCore.Signal()

    @property
    def selected_host_connection(self):
        return self.host_combobox.itemData(self.host_combobox.currentIndex())

    def __init__(self, client_name, parent=None):
        '''Initialize DefinitionSelector widget'''
        super(DefinitionSelectorWidgetBase, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._client_name = client_name
        self.host_connection = None
        self.schemas = None
        self._definition_title_filter = None
        self._definition_extensions_filter = None
        self.definitions = []

        self.host_connections = []
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

    def build(self):
        self.host_combobox = QtWidgets.QComboBox()
        self.definition_combobox = QtWidgets.QComboBox()

        self.layout().addWidget(self.host_combobox)
        self.layout().addWidget(self.definition_combobox)

        self.host_combobox.addItem('- Select host -')

    def post_build(self):
        '''Connect the widget signals'''
        self.host_combobox.currentIndexChanged.connect(self._on_change_host)
        self.definition_combobox.currentIndexChanged.connect(
            self._on_select_definition
        )

    def add_hosts(self, host_connections):
        for host_connection in host_connections:
            self.host_combobox.addItem(host_connection.name, host_connection)
            self.host_connections.append(host_connection)
        if (
            len(host_connections) == 1
            and host_connections[0].context_id != None
        ):
            self.host_combobox.setCurrentIndex(1)
        self.hostsDiscovered.emit(host_connections)

    def change_host_index(self, index):
        self.host_combobox.setCurrentIndex(index)

    def _on_change_host(self, index):
        '''triggered when changing host selection to *index*'''
        self.definition_combobox.clear()
        self.host_connection = self.host_combobox.itemData(index)
        self.hostChanged.emit(self.host_connection)

        if not self.host_connection:
            self.logger.debug('No data for selected host')
            return

        self.schemas = self.host_connection.definitions['schema']

        self.populate_definitions()

    def populate_definitions(self):
        self.definition_combobox.addItem('- Select Definition -')
        self.definitions = []
        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self._definition_title_filter:
                if schema_title != self._definition_title_filter:
                    continue
            items = self.host_connection.definitions.get(schema_title)
            self.definitions = items

            for item in items:
                text = '{}'.format(item.get('name'))
                if not self._definition_title_filter:
                    text = '{} - {}'.format(
                        schema.get('title'), item.get('name')
                    )
                self.definition_combobox.addItem(text, item)

        self.definition_combobox.show()

    def _on_select_definition(self, index):
        self.definition = self.definition_combobox.itemData(index)

        if not self.definition:
            self.logger.debug('No data for selected definition')
            self.definitionChanged.emit(None, None)
            return

        for schema in self.schemas:
            if (
                self.definition.get('type').lower()
                == schema.get('title').lower()
            ):
                self.schema = schema
                break

        self.definitionChanged.emit(self.schema, self.definition)

    def set_definition_title_filter(self, title_filter):
        self._definition_title_filter = title_filter

    def set_definition_extensions_filter(self, extensions_filter):
        self._definition_extensions_filter = extensions_filter

    def get_current_definition_index(self):
        return self.definition_combobox.currentIndex()

    def set_current_definition_index(self, index):
        self.definition_combobox.setCurrentIndex(index)
        self._on_select_definition(index)


class DefinitionSelectorWidgetButtons(DefinitionSelectorWidgetBase):
    '''DefinitionSelector as buttons on a row'''

    definitionChanged = QtCore.Signal(object, object, object)
    hostChanged = QtCore.Signal(object)
    max_column = 3

    def __init__(self, client_name, parent=None):
        '''Initialize DefinitionSelector widget'''
        super(DefinitionSelectorWidgetButtons, self).__init__(
            client_name, parent=parent
        )

    def build(self):
        self._label_text = "Choose what to {}".format(
            self._client_name.lower()
        )
        self._refresh_text = (
            "CLEAR" if self._client_name.lower() == "publish" else "REFRESH"
        )

        self.host_combobox = QtWidgets.QComboBox()

        self.definitions_widget = QtWidgets.QWidget()

        self.definitions_widget.setLayout(QtWidgets.QVBoxLayout())
        self.definitions_widget.layout().setContentsMargins(0, 0, 0, 0)

        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(QtWidgets.QHBoxLayout())
        header_widget.layout().setContentsMargins(0, 0, 0, 0)
        header_widget.layout().setSpacing(0)

        if self._client_name != 'assembler':
            self.label_widget = QtWidgets.QLabel(self._label_text)
            header_widget.layout().addWidget(self.label_widget)
            header_widget.layout().addStretch()

            self._refresh_button = QtWidgets.QPushButton(self._refresh_text)
            self._refresh_button.setObjectName('borderless')
            header_widget.layout().addWidget(self._refresh_button)

        header_widget.setVisible(self._client_name != 'assembler')

        self.definitions_widget.layout().addWidget(header_widget)

        self.button_group = QtWidgets.QButtonGroup(self)
        self.definition_buttons_widget = QtWidgets.QWidget()
        self.definition_buttons_widget.setLayout(QtWidgets.QHBoxLayout())
        self.definition_buttons_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.definition_buttons_widget.layout().setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self.definition_buttons_widget)

        self.definitions_widget.layout().addWidget(scroll)

        self.layout().addWidget(self.host_combobox)
        self.layout().addWidget(self.definitions_widget)
        self.definition_buttons_widget.setVisible(
            self._client_name != 'assembler'
        )

        self.no_definitions_label = QtWidgets.QLabel()
        self.layout().addWidget(self.no_definitions_label)
        self.no_definitions_label.setVisible(False)

        self.host_combobox.addItem('- Select host -')

    def post_build(self):
        '''Connect the widget signals'''
        self.host_combobox.currentIndexChanged.connect(self._on_change_host)
        if self._client_name != 'assembler':
            self._refresh_button.clicked.connect(self.refresh)

    def _on_change_host(self, index):
        '''triggered when changing host selection to *index*'''
        self.clear_definitions()
        self.host_connection = self.host_combobox.itemData(index)
        self.hostChanged.emit(self.host_connection)

        if not self.host_connection:
            self.logger.debug('No data for selected host')
            return

        self.schemas = self.host_connection.definitions['schema']
        self.populate_definitions()

    def clear_definitions(self):
        buttons = self.button_group.buttons()
        for button in buttons:
            self.button_group.removeButton(button)
            button.deleteLater()

    def populate_definitions(self):

        self.definitions = []

        latest_version = None  # The current latest version
        index_latest_version = -1

        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self._definition_title_filter:
                if schema_title != self._definition_title_filter:
                    continue
            items = self.host_connection.definitions.get(schema_title)
            self.definitions = items

            index = 0
            for item in items:
                # Remove ' Publisher/Loader'
                text = '{}'.format(' '.join(item.get('name').split(' ')[:-1]))
                component_names_filter = None  # Outlined openable components
                enable = True
                if self._client_name.lower() in [
                    qt_constants.OPEN_WIDGET,
                    qt_constants.ASSEMBLER_WIDGET,
                ]:
                    mode_filter = (
                        self._client_name.lower()
                        if self._client_name.lower()
                        != qt_constants.ASSEMBLER_WIDGET
                        else 'import'
                    )
                    # Remove plugins not matching client
                    # definition = copy.deepcopy(definition)
                    types = [
                        core_constants.CONTEXTS,
                        core_constants.COMPONENTS,
                        core_constants.FINALIZERS,
                    ]
                    for type_name in types:
                        for step in item[type_name]:
                            for stage in step['stages']:
                                plugins_remove = []
                                for plugin in stage['plugins']:
                                    mode = (plugin.get('mode') or '').lower()
                                    if mode != 'null' and mode != mode_filter:
                                        plugins_remove.append(plugin)
                                for plugin in plugins_remove:
                                    stage['plugins'].remove(plugin)
                if self._client_name == qt_constants.OPEN_WIDGET:
                    # Open mode; Only provide the schemas, and components that
                    # can load the file extensions. Peek into versions and pre-select
                    # the one loader having the latest version
                    for component_step in item['components']:
                        can_open_component = False
                        file_formats = component_step['file_formats']
                        if set(file_formats).intersection(
                            set(self._definition_extensions_filter)
                        ):
                            can_open_component = True
                        for stage in component_step['stages']:
                            for plugin in stage['plugins']:
                                if plugin.get('type') == 'importer':
                                    if not 'options' in plugin:
                                        plugin['options'] = {}
                                    plugin['options']['load_mode'] = 'Open'
                        if can_open_component:
                            if component_names_filter is None:
                                component_names_filter = set()
                            component_names_filter.add(component_step['name'])
                        else:
                            # Make sure it's not visible or executed
                            component_step['visible'] = False
                            component_step['enabled'] = False
                    if component_names_filter is None:
                        # There were no openable components, try next definition
                        continue
                if self._client_name == qt_constants.OPEN_WIDGET:
                    # Check if any versions at all, find out asset type name from package
                    asset_type_short = item['asset_type']
                    asset_version = None
                    # Package is referring to asset type code, find out name
                    asset_type_name = None
                    asset_type = self.host_connection.session.query(
                        'name from AssetType where short={}'.format(
                            asset_type_short
                        )
                    ).first()
                    if asset_type:
                        asset_type_name = asset_type['name']
                    else:
                        self.logger.warning(
                            'Cannot identify asset type name from short: {}'.format(
                                asset_type_short
                            )
                        )
                    if asset_type_name:
                        asset_version = self.host_connection.session.query(
                            'AssetVersion where '
                            'task.id={} and asset.type.name="{}" and is_latest_version=true'.format(
                                self.host_connection.context_id,
                                asset_type_name,
                            )
                        ).first()
                        if asset_version and (
                            latest_version is None
                            or latest_version['date'] < asset_version['date']
                        ):
                            latest_version = asset_version
                            index_latest_version = index
                    if (
                        asset_version is None
                        and self._client_name == qt_constants.OPEN_WIDGET
                    ):
                        enable = False
                if not self._definition_title_filter:
                    text = '{} - {}'.format(
                        schema.get('title'), item.get('name')
                    )
                definition_button = DefinitionItem(
                    text.upper(), item, component_names_filter
                )
                self.button_group.addButton(definition_button)
                definition_button.setEnabled(enable)
                self.definition_buttons_widget.layout().addWidget(
                    definition_button
                )
                definition_button.clicked.connect(
                    partial(self._on_select_definition, definition_button)
                )
                definition_button.setToolTip(json.dumps(item, indent=4))
                index += 1
        if (
            index_latest_version == -1
            and self._client_name == qt_constants.PUBLISHER_WIDGET
            and len(self.button_group.buttons()) == 1
        ):
            index_latest_version = 0  # Select the one and only
        if self.definition_buttons_widget.layout().count() == 0:
            if self._client_name == qt_constants.OPEN_WIDGET:
                self.no_definitions_label.setText(
                    '<html><i>No pipeline loader definitions available to open files of type {}!'
                    '</i></html>'.format(self._definition_extensions_filter)
                )
            elif self._client_name == qt_constants.PUBLISHER_WIDGET:
                self.no_definitions_label.setText(
                    '<html><i>No pipeline publisher definitions are available!</i></html>'
                )
            else:
                self.no_definitions_label.setText(
                    '<html><i>No pipeline loader definitions are available!</i></html>'
                )

            self.no_definitions_label.setVisible(True)
            self.definitionChanged.emit(
                None, None, None
            )  # Tell client there are no definitions
        elif index_latest_version == -1:
            if self._client_name == qt_constants.OPEN_WIDGET:
                # No versions
                self.no_definitions_label.setText(
                    '<html><i>No version available to open!</i></html>'
                )
                self.definitionChanged.emit(
                    None, None, None
                )  # Tell client there are no versions
        else:
            self.button_group.buttons()[index_latest_version].click()
            self.no_definitions_label.setVisible(False)
        self.definition_buttons_widget.layout().addStretch()
        if self._client_name != qt_constants.ASSEMBLER_WIDGET:
            self.definitions_widget.show()

    def _on_select_definition(self, definition_item):
        if definition_item:
            definition_item.setEnabled(False)
            for button in self.button_group.buttons():
                if not button is definition_item:
                    button.setEnabled(True)
            self.definition = definition_item.definition
            self.component_names_filter = (
                definition_item.component_names_filter
            )
        else:
            self.definition = None
        if not self.definition:
            self.logger.debug('No data for selected definition')
            self.definitionChanged.emit(None, None, None)
            return

        for schema in self.schemas:
            if (
                self.definition.get('type').lower()
                == schema.get('title').lower()
            ):
                self.schema = schema
                break

        self.definitionChanged.emit(
            self.schema, self.definition, self.component_names_filter
        )

    def get_current_definition_index(self):
        return self.button_group.checkedId()

    def set_current_definition_index(self, index):
        button = self.button_group.button(index)
        self._on_select_definition(button)

    def refresh(self):
        self._on_select_definition(self.button_group.checkedButton())
        self.refreshed.emit()


class DefinitionSelectorWidgetComboBox(DefinitionSelectorWidgetBase):
    '''DefinitionSelector Base Class'''

    definition_changed = QtCore.Signal(object, object, object)
    host_changed = QtCore.Signal(object)

    def __init__(self, client_name, parent=None):
        '''Initialize DefinitionSelector widget'''
        super(DefinitionSelectorWidgetComboBox, self).__init__(
            client_name, parent=parent
        )

    def build(self):
        self._label_text = "Choose what to {}".format(
            self._client_name.lower().replace('publisher', 'publish')
        )
        self._refresh_text = (
            "CLEAR" if self._client_name.lower() == "publish" else "REFRESH"
        )

        self.host_combobox = QtWidgets.QComboBox()

        self.definitions_widget = QtWidgets.QWidget()

        self.definitions_widget.setLayout(QtWidgets.QVBoxLayout())
        self.definitions_widget.layout().setContentsMargins(0, 0, 0, 0)

        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(QtWidgets.QHBoxLayout())
        header_widget.layout().setContentsMargins(0, 0, 0, 0)
        header_widget.layout().setSpacing(0)

        if self._client_name != 'assembler':
            self.label_widget = QtWidgets.QLabel(self._label_text)
            header_widget.layout().addWidget(self.label_widget)
            header_widget.layout().addStretch()

            self._refresh_button = QtWidgets.QPushButton(self._refresh_text)
            self._refresh_button.setObjectName('borderless')
            header_widget.layout().addWidget(self._refresh_button)

        header_widget.setVisible(self._client_name != 'assembler')

        self.definitions_widget.layout().addWidget(header_widget)

        self._definition_selector = DefinitionSelector()

        self.definitions_widget.layout().addWidget(self._definition_selector)

        self.layout().addWidget(self.host_combobox)
        self.layout().addWidget(self.definitions_widget)
        self.definitions_widget.setVisible(self._client_name != 'assembler')

        self.no_definitions_label = QtWidgets.QLabel()
        self.layout().addWidget(self.no_definitions_label)
        self.no_definitions_label.setVisible(False)

        self.host_combobox.addItem('- Select host -')

    def post_build(self):
        '''Connect the widget signals'''
        self.host_combobox.currentIndexChanged.connect(self._on_change_host)
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )
        if self._client_name != 'assembler':
            self._refresh_button.clicked.connect(self.refresh)

    def _on_change_host(self, index):
        '''triggered when changing host selection to *index*'''
        self.clear_definitions()
        self.host_connection = self.host_combobox.itemData(index)
        self.host_changed.emit(self.host_connection)

        if not self.host_connection:
            self.logger.debug('No data for selected host')
            return

        self.schemas = self.host_connection.definitions['schema']
        self.populate_definitions()

    def clear_definitions(self):
        self._definition_selector.currentIndexChanged.disconnect()
        self._definition_selector.clear()

    def populate_definitions(self):

        self.definitions = []

        latest_version = None  # The current latest version
        index_latest_version = -1

        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self._definition_title_filter:
                if schema_title != self._definition_title_filter:
                    continue
            items = self.host_connection.definitions.get(schema_title)
            self.definitions = items

            self._definition_selector.addItem("", None)
            index = 1

            for item in items:
                # Remove ' Publisher/Loader'
                text = '{}'.format(' '.join(item.get('name').split(' ')[:-1]))
                component_names_filter = None  # Outlined openable components
                enable = True
                if self._client_name.lower() in [
                    qt_constants.OPEN_WIDGET,
                    qt_constants.ASSEMBLER_WIDGET,
                ]:
                    mode_filter = (
                        self._client_name.lower()
                        if self._client_name.lower()
                        != qt_constants.ASSEMBLER_WIDGET
                        else 'import'
                    )
                    # Remove plugins not matching client
                    # definition = copy.deepcopy(definition)
                    types = [
                        core_constants.CONTEXTS,
                        core_constants.COMPONENTS,
                        core_constants.FINALIZERS,
                    ]
                    for type_name in types:
                        for step in item[type_name]:
                            for stage in step['stages']:
                                plugins_remove = []
                                for plugin in stage['plugins']:
                                    mode = (plugin.get('mode') or '').lower()
                                    if mode != 'null' and mode != mode_filter:
                                        plugins_remove.append(plugin)
                                for plugin in plugins_remove:
                                    stage['plugins'].remove(plugin)
                if self._client_name == qt_constants.OPEN_WIDGET:
                    # Open mode; Only provide the schemas, and components that
                    # can load the file extensions. Peek into versions and pre-select
                    # the one loader having the latest version
                    for component_step in item['components']:
                        can_open_component = False
                        file_formats = component_step['file_formats']
                        if set(file_formats).intersection(
                            set(self._definition_extensions_filter)
                        ):
                            can_open_component = True
                        for stage in component_step['stages']:
                            for plugin in stage['plugins']:
                                if plugin.get('type') == 'importer':
                                    if not 'options' in plugin:
                                        plugin['options'] = {}
                                    plugin['options']['load_mode'] = 'Open'
                        if can_open_component:
                            if component_names_filter is None:
                                component_names_filter = set()
                            component_names_filter.add(component_step['name'])
                        else:
                            # Make sure it's not visible or executed
                            component_step['visible'] = False
                            component_step['enabled'] = False
                    if component_names_filter is None:
                        # There were no openable components, try next definition
                        continue
                if self._client_name == qt_constants.OPEN_WIDGET:
                    # Check if any versions at all, find out asset type name from package
                    asset_type_short = item['asset_type']
                    asset_version = None
                    # Package is referring to asset type code, find out name
                    asset_type_name = None
                    asset_type = self.host_connection.session.query(
                        'AssetType where short={}'.format(asset_type_short)
                    ).first()
                    if asset_type:
                        asset_type_name = asset_type['name']
                    else:
                        self.logger.warning(
                            'Cannot identify asset type name from short: {}'.format(
                                asset_type_short
                            )
                        )
                    if asset_type_name:
                        asset_version = self.host_connection.session.query(
                            'AssetVersion where '
                            'task.id={} and asset.type.name="{}" and is_latest_version=true'.format(
                                self.host_connection.context_id,
                                asset_type_name,
                            )
                        ).first()
                        if asset_version and (
                            latest_version is None
                            or latest_version['date'] < asset_version['date']
                        ):
                            latest_version = asset_version
                            index_latest_version = index
                    if (
                        asset_version is None
                        and self._client_name == qt_constants.OPEN_WIDGET
                    ):
                        enable = False
                if not self._definition_title_filter:
                    text = '{} - {}'.format(
                        schema.get('title'), item.get('name')
                    )

                self._definition_selector.addItem(
                    text.upper(), (item, component_names_filter)
                )

                index += 1
        if (
            index_latest_version == -1
            and self._client_name == qt_constants.PUBLISHER_WIDGET
            and self._definition_selector.count() == 2
        ):
            index_latest_version = 1  # Select the one and only
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )
        if self._definition_selector.count() == 1:
            if self._client_name == qt_constants.OPEN_WIDGET:
                self.no_definitions_label.setText(
                    '<html><i>No pipeline loader definitions available to open files of type {}!'
                    '</i></html>'.format(self._definition_extensions_filter)
                )
            elif self._client_name == qt_constants.PUBLISHER_WIDGET:
                self.no_definitions_label.setText(
                    '<html><i>No pipeline publisher definitions are available!</i></html>'
                )
            else:
                self.no_definitions_label.setText(
                    '<html><i>No pipeline loader definitions are available!</i></html>'
                )

            self.no_definitions_label.setVisible(True)
            # self.definition_changed.emit(
            #    None, None, None
            # )  # Tell client there are no definitions
            self._definition_selector.setCurrentIndex(0)
        elif index_latest_version == -1:
            if self._client_name == qt_constants.OPEN_WIDGET:
                # No versions
                self.no_definitions_label.setText(
                    '<html><i>No version available to open!</i></html>'
                )
                self._definition_selector.setCurrentIndex(0)
                # self.definition_changed.emit(
                #    None, None, None
                # )  # Tell client there are no versions
        else:
            self._definition_selector.setCurrentIndex(index_latest_version)
            self.no_definitions_label.setVisible(False)
        if self._client_name != qt_constants.ASSEMBLER_WIDGET:
            self.definitions_widget.show()

    def _on_change_definition(self, index):
        if index > 0:
            (
                self.definition,
                self.component_names_filter,
            ) = self._definition_selector.itemData(index)
            self._definition_selector.setToolTip(
                json.dumps(self.definition, indent=4)
            )
        else:
            self._definition_selector.setToolTip(
                'Please select an importer definition.'
            )
            self.definition = self.component_names_filter = None
        if not self.definition:
            self.logger.debug('No data for selected definition')
            self.definition_changed.emit(None, None, None)
            return

        for schema in self.schemas:
            if (
                self.definition.get('type').lower()
                == schema.get('title').lower()
            ):
                self.schema = schema
                break
        self.definition_changed.emit(
            self.schema, self.definition, self.component_names_filter
        )

    def get_current_definition_index(self):
        return self._definition_selector.currentIndex()

    def set_current_definition_index(self, index):
        if self._definition_selector.currentIndex() != index:
            self._definition_selector.setCurrentIndex(index)
        else:
            self._on_change_definition(index)

    def refresh(self):
        self._on_change_definition(self._definition_selector.currentIndex())
        self.refreshed.emit()


class DefinitionSelector(QtWidgets.QComboBox):
    def __init__(self):
        super(DefinitionSelector, self).__init__()
