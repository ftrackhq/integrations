# :coding: utf-8
# :copyright: Copyright (c) 2015-2022 ftrack
import logging
import re

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)


class DefinitionSelectorBase(QtWidgets.QWidget):
    '''Definition selector base widget - enables user to select which definition to use for opening and publishing'''

    definitionChanged = QtCore.Signal(
        object, object, object
    )  # User has selected a definition, or no definition is selectable

    refreshed = QtCore.Signal()  # Widget has been refreshed

    @property
    def definition_filters(self):
        '''Return the list of definition title filters'''
        return self._definition_filters

    @definition_filters.setter
    def definition_filters(self, value):
        '''Set the list of definition title filters to *value*'''
        self._definition_filters = value

    @property
    def definition_extensions_filter(self):
        '''Return the list of component filename extension filters, e.g. [".ma",".mb"]'''
        return self._definition_extensions_filter

    @definition_extensions_filter.setter
    def definition_extensions_filter(self, value):
        '''Set the list of component filename extension filter to *value*'''
        self._definition_extensions_filter = value

    @property
    def current_definition_index(self):
        '''Return the current index of selected definition, 1-based (0 is no definition selected)'''
        return self._definition_selector.currentIndex()

    @current_definition_index.setter
    def current_definition_index(self, value):
        '''Set the current index of selected definition to *value*'''
        if self._definition_selector.currentIndex() != value:
            self._definition_selector.setCurrentIndex(value)
        else:
            self._on_change_definition(value)

    def __init__(self, parent=None):
        '''
        Initialize DefinitionSelector widget

        :param parent: The parent dialog or frame
        '''
        super(DefinitionSelectorBase, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._host_connection = None
        self.schemas = None
        self._definition_filters = None
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
        '''Build the main widget'''
        self._definition_widget = QtWidgets.QWidget()

        self._definition_widget.setLayout(QtWidgets.QVBoxLayout())
        self._definition_widget.layout().setContentsMargins(0, 0, 0, 0)

        definition_select_widget = QtWidgets.QWidget()
        definition_select_widget.setLayout(QtWidgets.QHBoxLayout())
        definition_select_widget.layout().setContentsMargins(0, 0, 0, 0)
        definition_select_widget.layout().setSpacing(10)

        definition_select_widget.layout().addWidget(self.label_widget)
        self._definition_selector = DefinitionSelectorComboBox()
        self._definition_selector.setToolTip(self.label_widget.text())

        definition_select_widget.layout().addWidget(
            self._definition_selector, 10
        )

        self._refresh_button = CircularButton('sync')
        definition_select_widget.layout().addWidget(self._refresh_button)

        self._definition_widget.layout().addWidget(definition_select_widget)
        return self._definition_widget

    def post_build(self):
        '''Connect the widget signals'''
        self.no_definitions_label.setVisible(False)

    def on_host_changed(self, host_connection):
        '''Called when client has set the host connection and thus provided the schemas/definitions'''
        self.clear_definitions()
        self._host_connection = host_connection

        if not self._host_connection:
            self.logger.debug('No data for selected host')
            return

        self.schemas = self._host_connection.definitions['schema']

    def clear_definitions(self):
        '''Remove all definitions and prepare for re-populate. Disconnects
        signals so we do not get any unwanted events during build'''
        self._definition_selector.clear()

    def populate_definitions(self):
        '''Host has been selected, fill up basic definition selector combobox with
        compatible definitions.'''
        raise NotImplementedError()

    def do_add_empty_definition(self):
        '''Add an empty definition to the definition selector'''
        return True

    def _on_change_definition(self, index):
        '''A definition has been selected, fire signal for client to pick up'''
        self.definitionChanged.emit(None, None, None)  # Clear widgets
        if index > 0 if self.do_add_empty_definition() else -1:
            (
                self.definition,
                self.component_names_filter,
            ) = self._definition_selector.itemData(index)
            # Locate the schema for definition
            for schema in self.schemas:
                if (
                    self.definition.get('type').lower()
                    == schema.get('title').lower()
                ):
                    self.schema = schema
                    break
            self.definitionChanged.emit(
                self.definition, self.schema, self.component_names_filter
            )
        else:
            self.logger.debug('No data for selected definition')
            self.definition = self.component_names_filter = None

    def refresh(self):
        '''Refresh the widget'''
        self._on_change_definition(self._definition_selector.currentIndex())
        self.refreshed.emit()


class OpenerDefinitionSelector(DefinitionSelectorBase):
    '''Definition selector tailored for opener client'''

    def __init__(self, parent=None):
        super(OpenerDefinitionSelector, self).__init__(parent=parent)

    def pre_build(self):
        super(OpenerDefinitionSelector, self).pre_build()
        self.label_widget = QtWidgets.QLabel("Choose what to open")

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

        if self._host_connection.context_id is None:
            self.logger.warning(
                'Not able to populate definitions - no context set!'
            )
            return

        latest_version = None  # The current latest openable version
        index_latest_version = -1
        compatible_definition_count = 0

        index = 0
        if self.do_add_empty_definition():
            self._definition_selector.addItem("", None)
            index += 1

        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self.definition_filters:
                if not schema_title in self.definition_filters:
                    continue
            items = self._host_connection.definitions.get(schema_title)
            self.definitions = items

            for item in items:
                # Remove ' Publisher/Loader'
                text = '{}'.format(' '.join(item.get('name').split(' ')[:-1]))
                component_names_filter = None  # Outlined openable components
                # Open mode; Only provide the schemas, and components that
                # can load the file extensions. Peek into versions and pre-select
                # the one loader having the latest version
                is_compatible = False
                for component_step in item.get_all(
                    type=core_constants.COMPONENT
                ):
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

                component_names_filter_low = list(
                    map(str.lower, component_names_filter)
                )
                # Check if any versions at all, find out asset type name from package
                asset_type_short = item['asset_type']
                for asset_version in self._host_connection.session.query(
                    'select components.name,components.file_type,date,version,asset.id,asset.name,task.context_type,task.id,task.name from AssetVersion where '
                    'task.id={} and asset.type.short="{}" order by date descending'.format(
                        self._host_connection.context_id,
                        asset_type_short,
                    )
                ):
                    version_has_openable_component = False
                    for component in asset_version['components']:
                        if (
                            component['name'].lower()
                            in component_names_filter_low
                        ):
                            # Check if file extension matches
                            if (
                                component['file_type']
                                in self._definition_extensions_filter
                            ):
                                version_has_openable_component = True
                                break

                    if version_has_openable_component:
                        self.logger.info(
                            'Version {} can be opened'.format(
                                str_version(asset_version)
                            )
                        )
                        if (
                            latest_version is None
                            or latest_version['date'] < asset_version['date']
                        ):
                            latest_version = asset_version
                            index_latest_version = index
                        break
                if not self.definition_filters:
                    text = '{} - {}'.format(
                        schema.get('title'), item.get('name')
                    )
                self._definition_selector.addItem(
                    text.upper(), (item, component_names_filter)
                )
                index += 1
            break  # Done with schemas

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
            self.definitionChanged.emit(None, None, None)  # Have client react
        elif index_latest_version == -1:
            # No version were detected
            self.no_definitions_label.setText(
                '<html><i>No version(s) available to open!</i></html>'
            )
            self.no_definitions_label.setVisible(True)
            self._definition_selector.setCurrentIndex(0)
            self.definitionChanged.emit(None, None, None)  # Have client react
        else:
            self._definition_selector.setCurrentIndex(index_latest_version)

        self._definition_widget.show()


class AssemblerDefinitionSelector(DefinitionSelectorBase):
    '''Definition selector tailored for assembler(loader) client.
    Selection of definitions are disabled, widget is only used for extraction of definitions
    '''

    def __init__(self, parent=None):
        super(AssemblerDefinitionSelector, self).__init__(parent=parent)

    def post_build(self):
        super(AssemblerDefinitionSelector, self).post_build()
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )
        self.label_widget.setVisible(False)
        self._definition_widget.setVisible(False)

    def populate_definitions(self):
        '''(Override) Simply extract and store loader definitions from schemas'''
        if self.schemas is None:
            self.logger.warning(
                'Not able to populate definitions - no schemas available!'
            )
            return
        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self.definition_filters:
                if not schema_title in self.definition_filters:
                    continue
            items = self._host_connection.definitions.get(schema_title)
            self.definitions = items


class PublisherDefinitionSelector(DefinitionSelectorBase):
    '''Definition selector tailored for publisher client'''

    def __init__(self, parent=None):
        super(PublisherDefinitionSelector, self).__init__(parent=parent)

    def pre_build(self):
        super(PublisherDefinitionSelector, self).pre_build()
        self.label_widget = QtWidgets.QLabel("Select publisher")

    def post_build(self):
        super(PublisherDefinitionSelector, self).post_build()
        self._refresh_button.clicked.connect(self.refresh)
        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )

    def populate_definitions(self):
        '''Find publisher schemas and add their definitions to combobox'''
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

        self._definition_selector.addItem("- please choose -", None)
        index = 1

        for schema in self.schemas:
            schema_title = schema.get('title').lower()
            if self.definition_filters:
                if not schema_title in self.definition_filters:
                    continue
            items = self._host_connection.definitions.get(schema_title)
            self.definitions = items

            for item in items:
                # Remove ' Publisher/Loader'
                text = '{}'.format(' '.join(item.get('name').split(' ')[:-1]))
                component_names_filter = None

                if not self.definition_filters:
                    text = '{} - {}'.format(
                        schema.get('title'), item.get('name')
                    )
                self._definition_selector.addItem(
                    text.upper(), (item, component_names_filter)
                )
                index += 1
            break

        self._definition_selector.currentIndexChanged.connect(
            self._on_change_definition
        )
        self.no_definitions_label.setVisible(False)
        if index == 1:
            # No compatible definitions
            self.no_definitions_label.setText(
                '<html><i style="color:red;">No pipeline publisher definitions are available!</i></html>'
            )

            self.no_definitions_label.setVisible(True)
            self._definition_selector.setCurrentIndex(0)

        self._definition_widget.show()


class DefinitionSelectorComboBox(QtWidgets.QComboBox):
    def __init__(self, parent=None):
        super(DefinitionSelectorComboBox, self).__init__(parent=parent)
