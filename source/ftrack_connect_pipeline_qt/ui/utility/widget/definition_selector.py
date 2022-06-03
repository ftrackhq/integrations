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


class DefinitionSelectorBase(QtWidgets.QWidget):
    '''Definition selector widget.'''

    definitionChanged = QtCore.Signal(object, object, object)
    refreshed = QtCore.Signal()

    @property
    def definition_title_filters(self):
        return self._definition_title_filters

    @definition_title_filters.setter
    def definition_title_filters(self, value):
        self._definition_title_filters = value

    @property
    def definition_extensions_filter(self):
        return self._definition_extensions_filter

    @definition_extensions_filter.setter
    def definition_extensions_filter(self, value):
        self._definition_extensions_filter = value

    @property
    def current_definition_index(self):
        return self._definition_selector.currentIndex()

    @current_definition_index.setter
    def current_definition_index(self, value):
        if self._definition_selector.currentIndex() != value:
            self._definition_selector.setCurrentIndex(value)
        else:
            self._on_change_definition(value)

    def __init__(self, parent=None):
        '''Initialize DefinitionSelector widget'''
        super(DefinitionSelectorBase, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._host_connection = None
        self.schemas = None
        self._definition_title_filters = None
        self._definition_extensions_filter = None
        self.definitions = []

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.label_widget = QtWidgets.QLabel()

    def build(self):
        # Definition section
        self.layout().addWidget(self.build_definition_widget())

        self.no_definitions_label = QtWidgets.QLabel()
        self.layout().addWidget(self.no_definitions_label)

    def build_definition_widget(self):
        raise NotImplementedError()

    def post_build(self):
        '''Connect the widget signals'''
        self.no_definitions_label.setVisible(False)

    def on_host_changed(self, host_connection):
        '''Triggered when client has set host connection'''
        self.clear_definitions()
        self._host_connection = host_connection

        if not self._host_connection:
            self.logger.debug('No data for selected host')
            return

        self.schemas = self._host_connection.definitions['schema']
        self.populate_definitions()

    def clear_definitions(self):
        '''Remove all definitions and prepare for re-populate. Disconnects
        signals so we do not get any unwanted events during build'''
        self._definition_selector.clear()

    def populate_definitions(self):
        '''Host has been selected, fill up basic definition selector combobox with
        compatible definitions.'''
        raise NotImplementedError()

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

    def refresh(self):
        self._on_change_definition(self._definition_selector.currentIndex())
        self.refreshed.emit()


class OpenerDefinitionSelector(DefinitionSelectorBase):
    def __init__(self, parent=None):
        super(OpenerDefinitionSelector, self).__init__(parent=parent)

    def pre_build(self):
        super(OpenerDefinitionSelector, self).pre_build()
        self.label_widget = QtWidgets.QLabel("Choose what to open")

    def build_definition_widget(self):
        self._definition_widget = QtWidgets.QWidget()

        self._definition_widget.setLayout(QtWidgets.QVBoxLayout())
        self._definition_widget.layout().setContentsMargins(0, 0, 0, 0)

        definition_select_widget = QtWidgets.QWidget()
        definition_select_widget.setLayout(QtWidgets.QHBoxLayout())
        definition_select_widget.layout().setContentsMargins(0, 0, 0, 0)
        definition_select_widget.layout().setSpacing(10)

        definition_select_widget.layout().addWidget(self.label_widget)
        self._definition_selector = DefinitionSelectorComboBox()

        definition_select_widget.layout().addWidget(
            self._definition_selector, 10
        )

        self._refresh_button = CircularButton('sync')
        definition_select_widget.layout().addWidget(self._refresh_button)

        self._definition_widget.layout().addWidget(definition_select_widget)
        return self._definition_widget

    def post_build(self):
        super(OpenerDefinitionSelector, self).post_build()
        self._refresh_button.clicked.connect(self.refresh)
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )

    def populate_definitions(self):
        '''Find components that can be opened and add their definitions to combobox'''
        try:
            self._definition_selector.currentIndexChanged.disconnect()
        except:
            pass

        self.definitions = []

        if self.schemas is None:
            self.logger.warning(
                'Not able to populate definitions - no schemas available!'
            )
            return

        latest_version = None  # The current latest openable version
        index_latest_version = -1
        compatible_definition_count = 0

        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self._definition_title_filters:
                if not schema_title in self._definition_title_filters:
                    continue
            items = self._host_connection.definitions.get(schema_title)
            self.definitions = items

            self._definition_selector.addItem("", None)
            index = 1

            for item in items:
                # Remove ' Publisher/Loader'
                text = '{}'.format(' '.join(item.get('name').split(' ')[:-1]))
                component_names_filter = None  # Outlined openable components
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
                else:
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
                asset_type = self._host_connection.session.query(
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
                    asset_version = self._host_connection.session.query(
                        'AssetVersion where '
                        'task.id={} and asset.type.name="{}" and is_latest_version=true'.format(
                            self._host_connection.context_id,
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
                            or latest_version['date'] < asset_version['date']
                        ):
                            latest_version = asset_version
                            index_latest_version = index
                            self.logger.info(
                                'Version {} can be opened'.format(
                                    str_version(asset_version)
                                )
                            )
                if not self._definition_title_filters:
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
        self.no_definitions_label.setVisible(False)
        if compatible_definition_count == 0:
            # No compatible definitions
            self.no_definitions_label.setText(
                '<html><i>No pipeline opener definitions available to open files of type {}!'
                '</i></html>'.format(self._definition_extensions_filter)
            )

            self.no_definitions_label.setVisible(True)
            self._definition_selector.setCurrentIndex(0)
        elif index_latest_version == -1:
            # No version were detected
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

        self._definition_widget.show()


class AssemblerDefinitionSelector(DefinitionSelectorBase):
    def __init__(self, parent=None):
        super(AssemblerDefinitionSelector, self).__init__(parent=parent)

    def build_definition_widget(self):
        '''Not used in assembler, build dummy.'''
        self._definition_widget = QtWidgets.QWidget()
        self._definition_widget.setLayout(QtWidgets.QHBoxLayout())
        self._definition_selector = DefinitionSelectorComboBox()
        self._definition_widget.layout().addWidget(self._definition_selector)
        return self._definition_widget

    def post_build(self):
        super(AssemblerDefinitionSelector, self).post_build()
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )
        self.label_widget.setVisible(False)
        self._definition_widget.setVisible(False)

    def populate_definitions(self):
        '''(Override)'''
        pass


class PublisherDefinitionSelector(DefinitionSelectorBase):
    def __init__(self, parent=None):
        super(PublisherDefinitionSelector, self).__init__(parent=parent)

    def pre_build(self):
        super(PublisherDefinitionSelector, self).pre_build()
        self.label_widget = QtWidgets.QLabel("Choose what to publish")

    def build_definition_widget(self):
        self._definition_widget = QtWidgets.QWidget()

        self._definition_widget.setLayout(QtWidgets.QVBoxLayout())
        self._definition_widget.layout().setContentsMargins(0, 0, 0, 0)

        definition_select_widget = QtWidgets.QWidget()
        definition_select_widget.setLayout(QtWidgets.QHBoxLayout())
        definition_select_widget.layout().setContentsMargins(0, 0, 0, 0)
        definition_select_widget.layout().setSpacing(10)

        definition_select_widget.layout().addWidget(self.label_widget)
        self._definition_selector = DefinitionSelectorComboBox()

        definition_select_widget.layout().addWidget(
            self._definition_selector, 10
        )

        self._refresh_button = CircularButton('sync')
        definition_select_widget.layout().addWidget(self._refresh_button)

        self._definition_widget.layout().addWidget(definition_select_widget)
        return self._definition_widget

    def post_build(self):
        super(PublisherDefinitionSelector, self).post_build()
        self._refresh_button.clicked.connect(self.refresh)
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )

    def populate_definitions(self):
        '''Find components that can be opened and add their definitions to combobox'''
        try:
            self._definition_selector.currentIndexChanged.disconnect()
        except:
            pass

        self.definitions = []

        if self.schemas is None:
            self.logger.warning(
                'Not able to populate definitions - no schemas available!'
            )
            return

        latest_version = None  # The current latest openable version
        index_latest_version = -1
        compatible_definition_count = 0

        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self._definition_title_filters:
                if not schema_title in self._definition_title_filters:
                    continue
            items = self._host_connection.definitions.get(schema_title)
            self.definitions = items

            self._definition_selector.addItem("", None)
            index = 1

            for item in items:
                # Remove ' Publisher/Loader'
                text = '{}'.format(' '.join(item.get('name').split(' ')[:-1]))
                component_names_filter = None  # Outlined openable components

                if not self._definition_title_filters:
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
        self.no_definitions_label.setVisible(False)
        if compatible_definition_count == 0:
            # No compatible definitions
            self.no_definitions_label.setText(
                '<html><i>No pipeline publisher definitions are available!</i></html>'
            )

            self.no_definitions_label.setVisible(True)
            self._definition_selector.setCurrentIndex(0)
        elif index_latest_version == -1:
            # No version were detected
            pass
        else:
            self._definition_selector.setCurrentIndex(index_latest_version)

        self._definition_widget.show()


class DefinitionSelectorComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(DefinitionSelectorComboBox, self).__init__(parent=parent)
