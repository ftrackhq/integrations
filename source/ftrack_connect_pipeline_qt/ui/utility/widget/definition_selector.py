import logging
import json
import copy
from functools import partial

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt import constants as qt_constants

from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)


class DefinitionSelector(QtWidgets.QWidget):
    '''Host and definition selector widget. Hides the host input
    if only one host (default usage scenario within DCCs).'''

    hostsDiscovered = QtCore.Signal(object)
    hostChanged = QtCore.Signal(object)
    definitionChanged = QtCore.Signal(object, object, object)
    refreshed = QtCore.Signal()

    @property
    def selected_host_connection(self):
        return self._host_combobox.itemData(self._host_combobox.currentIndex())

    def __init__(self, client_name, parent=None):
        '''Initialize DefinitionSelector widget'''
        super(DefinitionSelector, self).__init__(parent=parent)

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
        # Host section
        self.host_widget = QtWidgets.QWidget()
        self.host_widget.setLayout(QtWidgets.QHBoxLayout())
        self.host_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.host_widget.layout().setSpacing(10)

        l_host = QtWidgets.QLabel('Select host:')
        l_host.setObjectName('gray')
        self.host_widget.layout().addWidget(l_host)

        self._host_combobox = QtWidgets.QComboBox()
        self._host_combobox.addItem('- Select host -')
        self.host_widget.layout().addWidget(self._host_combobox, 10)

        self.layout().addWidget(self.host_widget)

        self._definition_widget = QtWidgets.QWidget()

        self._definition_widget.setLayout(QtWidgets.QVBoxLayout())
        self._definition_widget.layout().setContentsMargins(0, 0, 0, 0)

        # Definition section
        self.label_widget = QtWidgets.QLabel(
            "Choose what to {}".format(
                self._client_name.lower().replace(
                    qt_constants.PUBLISHER_WIDGET, 'publish'
                )
            )
        )
        if self._client_name == qt_constants.PUBLISHER_WIDGET:
            self._definition_widget.layout().addWidget(self.label_widget)

        definition_select_widget = QtWidgets.QWidget()
        definition_select_widget.setLayout(QtWidgets.QHBoxLayout())
        definition_select_widget.layout().setContentsMargins(0, 0, 0, 0)
        definition_select_widget.layout().setSpacing(10)

        if self._client_name == qt_constants.OPEN_WIDGET:
            definition_select_widget.layout().addWidget(self.label_widget)
        self._definition_selector = DefinitionSelectorComboBox()

        definition_select_widget.layout().addWidget(
            self._definition_selector, 10
        )

        self._refresh_button = CircularButton('sync')
        definition_select_widget.layout().addWidget(self._refresh_button)

        self._definition_widget.layout().addWidget(definition_select_widget)

        self.layout().addWidget(self._definition_widget)

        self.no_definitions_label = QtWidgets.QLabel()
        self.layout().addWidget(self.no_definitions_label)

    def post_build(self):
        '''Connect the widget signals'''
        self._host_combobox.currentIndexChanged.connect(self._on_change_host)
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )
        if self._client_name != 'assembler':
            self._refresh_button.clicked.connect(self.refresh)
        self.label_widget.setVisible(
            self._client_name != qt_constants.ASSEMBLER_WIDGET
        )
        self._definition_widget.setVisible(
            self._client_name != qt_constants.ASSEMBLER_WIDGET
        )
        self.no_definitions_label.setVisible(False)

    def add_hosts(self, host_connections):
        '''Ass host connections to combobox for user selection'''
        for host_connection in host_connections:
            self._host_combobox.addItem(host_connection.name, host_connection)
            self.host_connections.append(host_connection)
        if (
            len(host_connections) == 1
            and host_connections[0].context_id != None
        ):
            self._host_combobox.setCurrentIndex(1)
        self.hostsDiscovered.emit(host_connections)

    def _on_change_host(self, index):
        '''triggered when changing host selection to *index*'''
        self.clear_definitions()
        self.host_connection = self._host_combobox.itemData(index)
        self.hostChanged.emit(self.host_connection)

        if not self.host_connection:
            self.logger.debug('No data for selected host')
            return

        self.schemas = self.host_connection.definitions['schema']
        self.populate_definitions()

    def clear_definitions(self):
        '''Remove all definitions and prepare for re-populate. Disconnects
        signals so we do not get any unwanted events during build'''
        self._definition_selector.currentIndexChanged.disconnect()
        self._definition_selector.clear()

    def populate_definitions(self):
        '''Host has been selected, fill up definition selector combobox with
        compatible definitions.'''
        self.definitions = []

        latest_version = None  # The current latest openable version
        index_latest_version = -1
        compatible_definition_count = 0

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
                    is_compatible = False
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
                            is_compatible = True
                            if component_names_filter is None:
                                component_names_filter = set()
                            component_names_filter.add(component_step['name'])
                        else:
                            # Make sure it's not visible or executed
                            component_step['visible'] = False
                            component_step['enabled'] = False
                    if is_compatible:
                        compatible_definition_count += 1
                    if component_names_filter is None:
                        # There were no openable components, try next definition
                        self.logger.info(
                            'No openable components exists for definition "{}"!'.format(
                                item.get('name')
                            )
                        )
                        continue

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
                        if asset_version:
                            version_has_openable_component = False
                            for component in asset_version['components']:
                                for component_name in component_names_filter:
                                    if (
                                        component['name'].lower()
                                        == component_name.lower()
                                    ):
                                        version_has_openable_component = True
                                        break
                                if version_has_openable_component:
                                    break
                            if version_has_openable_component and (
                                latest_version is None
                                or latest_version['date']
                                < asset_version['date']
                            ):
                                latest_version = asset_version
                                index_latest_version = index
                                self.logger.info(
                                    'Version {} can be opened'.format(
                                        str_version(asset_version)
                                    )
                                )
                if not self._definition_title_filter:
                    text = '{} - {}'.format(
                        schema.get('title'), item.get('name')
                    )
                self._definition_selector.addItem(
                    text.upper(), (item, component_names_filter)
                )
                index += 1
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )
        if compatible_definition_count == 0:
            # No compatible loaders/publishers
            if self._client_name == qt_constants.OPEN_WIDGET:
                self.no_definitions_label.setText(
                    '<html><i>No pipeline loader definitions available to open files of type {}!'
                    '</i></html>'.format(self._definition_extensions_filter)
                )
            elif self._client_name == qt_constants.PUBLISHER_WIDGET:
                self.no_definitions_label.setText(
                    '<html><i>No pipeline publisher definitions are available!</i></html>'
                )

            self.no_definitions_label.setVisible(True)
            self._definition_selector.setCurrentIndex(0)
        elif index_latest_version == -1:
            # No version were detected
            if self._client_name == qt_constants.OPEN_WIDGET:
                self.no_definitions_label.setText(
                    '<html><i>No version(s) available to open!</i></html>'
                )
                self.no_definitions_label.setVisible(True)
                self._definition_selector.setCurrentIndex(0)
                self.definitionChanged.emit(
                    None, None, None
                )  # Tell client there are no versions
        else:
            self._definition_selector.setCurrentIndex(index_latest_version)
            self.no_definitions_label.setVisible(False)

        if self._client_name != qt_constants.ASSEMBLER_WIDGET:
            self._definition_widget.show()

    def _on_change_definition(self, index):
        '''A definition has been selected, fire signal for client to pick up'''
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

    def set_definition_title_filter(self, title_filter):
        '''Set the *title_filter* name filter to use when populating definitions'''
        self._definition_title_filter = title_filter

    def set_definition_extensions_filter(self, extensions_filter):
        '''Set the *extensions_filter* (file_type:s) filter to use when populating definitions'''
        self._definition_extensions_filter = extensions_filter

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


class DefinitionSelectorComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(DefinitionSelectorComboBox, self).__init__(parent=parent)
