# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
import json
import time
import logging
import copy

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.client import constants
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetListModel,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetListWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    AssetVersion,
)
from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.asset_manager import (
    AssetVersionStatusWidget,
)
from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline_qt.utils import (
    set_property,
    clear_layout,
    get_main_framework_window_from_widget,
)

from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.ui.utility.widget.options_button import (
    OptionsButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    icon,
    overlay,
    scroll_area,
)


class AssemblerBaseWidget(QtWidgets.QWidget):
    '''Base assembler dependency or browse widget'''

    stopBusyIndicator = QtCore.Signal()

    @property
    def component_list(self):
        '''Return the collected object by the widget'''
        return self._component_list

    @property
    def session(self):
        return self._assembler_client.session

    @property
    def match_component_names(self):
        return self._rb_match_component_name.isChecked()

    @property
    def show_non_compatible_assets(self):
        return self._cb_show_non_compatible.isChecked()

    def __init__(self, assembler_client, parent=None):
        super(AssemblerBaseWidget, self).__init__(parent=parent)
        self._assembler_client = assembler_client
        self._component_list = None
        self._loadable_count = -1

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.pre_build()
        self.build_header()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(1, 0, 1, 0)
        self.layout().setSpacing(0)
        self.model = AssetListModel(self._assembler_client.event_manager)

    def build_header(self):
        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(QtWidgets.QVBoxLayout())
        header_widget.layout().setContentsMargins(4, 4, 4, 4)
        header_widget.layout().setSpacing(2)

        top_toolbar_widget = QtWidgets.QWidget()
        top_toolbar_widget.setLayout(QtWidgets.QHBoxLayout())
        top_toolbar_widget.layout().setContentsMargins(4, 4, 4, 4)
        top_toolbar_widget.layout().setSpacing(4)

        top_toolbar_widget.layout().addWidget(self._get_header_widget(), 10)

        header_widget.layout().addWidget(top_toolbar_widget)

        self.layout().addWidget(header_widget)

        # Add toolbar

        bottom_toolbar_widget = QtWidgets.QWidget()
        bottom_toolbar_widget.setLayout(QtWidgets.QHBoxLayout())
        bottom_toolbar_widget.layout().setContentsMargins(4, 1, 4, 1)
        bottom_toolbar_widget.layout().setSpacing(6)

        match_label = QtWidgets.QLabel('Match: ')
        match_label.setObjectName('gray')
        bottom_toolbar_widget.layout().addWidget(match_label)

        self._bg_match = QtWidgets.QButtonGroup(self)
        self._rb_match_component_name = QtWidgets.QRadioButton(
            'Component name'
        )
        self._rb_match_component_name.setToolTip(
            'Matching assets strictly on component names as defined in loader definitions.'
        )
        self._bg_match.addButton(self._rb_match_component_name)
        bottom_toolbar_widget.layout().addWidget(self._rb_match_component_name)

        self._rb_match_extension = QtWidgets.QRadioButton('File format')
        self._rb_match_extension.setToolTip(
            'Matching assets on supported file formats as defined in loader definitions(relaxed).'
        )
        self._bg_match.addButton(self._rb_match_extension)
        bottom_toolbar_widget.layout().addWidget(self._rb_match_extension)

        bottom_toolbar_widget.layout().addWidget(QtWidgets.QLabel(' '))

        self._cb_show_non_compatible = QtWidgets.QCheckBox('Show all')
        self._cb_show_non_compatible.setToolTip(
            'Show all assets, regardless if they can be loaded or not.'
        )
        self._cb_show_non_compatible.setObjectName("gray")
        bottom_toolbar_widget.layout().addWidget(self._cb_show_non_compatible)

        bottom_toolbar_widget.layout().addWidget(QtWidgets.QLabel(), 10)

        self._label_info = QtWidgets.QLabel('')
        self._label_info.setObjectName('gray-darker')
        bottom_toolbar_widget.layout().addWidget(self._label_info)

        self._search = Search()
        bottom_toolbar_widget.layout().addWidget(self._search)

        self._rebuild_button = CircularButton('sync', '#87E1EB')
        bottom_toolbar_widget.layout().addWidget(self._rebuild_button)

        self._busy_widget = BusyIndicator(start=False)
        self._busy_widget.setMinimumSize(QtCore.QSize(16, 16))
        self._busy_widget.setVisible(False)
        bottom_toolbar_widget.layout().addWidget(self._busy_widget)

        header_widget.layout().addWidget(bottom_toolbar_widget)

    def build(self):
        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setStyle(QtWidgets.QStyleFactory.create("plastique"))

        self.layout().addWidget(self.scroll, 1000)

    def rebuild(self):

        self._rb_match_component_name.setEnabled(
            not self._cb_show_non_compatible.isChecked()
        )
        self._rb_match_extension.setEnabled(
            not self._cb_show_non_compatible.isChecked()
        )
        self.model.reset()
        self._assembler_client.progress_widget.hide_widget()

        self._busy_widget.start()
        self._rebuild_button.setVisible(False)
        self._busy_widget.setVisible(True)

        self._label_info.setText('Fetching...')

        # Wait for context to be loaded
        self.get_context()

        self._loadable_count = 0

    def post_build(self):
        self._cb_show_non_compatible.clicked.connect(self.rebuild)
        if self._assembler_client.assembler_match_extension:
            self._rb_match_extension.setChecked(True)
        else:
            self._rb_match_component_name.setChecked(True)
        self._rb_match_component_name.clicked.connect(self.rebuild)
        self._rb_match_extension.clicked.connect(self.rebuild)
        self.stopBusyIndicator.connect(self._stop_busy_indicator)

    def _stop_busy_indicator(self):
        self._busy_widget.stop()
        self._busy_widget.setVisible(False)
        self._rebuild_button.setVisible(True)

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.RightButton and self._component_list:
            self._component_list.clear_selection()
        return super(AssemblerBaseWidget, self).mousePressEvent(event)

    def get_context(self, wait=True):
        '''Wait for current working context to be properly set, then return it.'''
        while (
            self._assembler_client.context_selector.context_id is None and wait
        ):
            time.sleep(0.5)
        return self._assembler_client.context_selector.entity

    def extract_components(self, versions):
        '''Build a list of loadable components from the supplied *versions*'''

        # Fetch all definitions, append asset type name
        loader_definitions = (
            self._assembler_client.host_and_definition_selector.definitions
        )

        # import json
        self._assembler_client.logger.debug(
            'Available loader definitions: {}'.format(
                '\n'.join(
                    [
                        json.dumps(loader, indent=4)
                        for loader in loader_definitions
                    ]
                )
            )
        )

        # For each version, figure out loadable components and store with
        # fragment of its possible loader definition(s)

        components = []

        location = self.session.pick_location()

        # Group by context, sort by asset name
        for version in sorted(
            versions,
            key=lambda v: '{}/{}'.format(
                v['asset']['parent']['id'], v['asset']['name']
            ),
        ):
            self._assembler_client.logger.debug(
                'Processing version: {}'.format(
                    str_version(version, with_id=True)
                )
            )

            for component in version['components']:
                component_extension = component.get('file_type')
                self._assembler_client.logger.debug(
                    '     Processing component: {}({})'.format(
                        component['name'], component['file_type']
                    )
                )
                if not component_extension:
                    self.logger.warning(
                        'Could not assemble version {} component {}; missing file type!'.format(
                            version['id'], component['id']
                        )
                    )
                    continue
                elif not self.show_non_compatible_assets:
                    if (
                        component['name']
                        == core_constants.SNAPSHOT_COMPONENT_NAME
                    ):
                        self.logger.warning(
                            'Not assembling version {} snapshot component {}!'.format(
                                version['id'], component['id']
                            )
                        )
                        continue
                    elif component['name'].startswith(
                        core_constants.SNAPSHOT_FTRACKREVIEW_NAME
                    ):
                        self.logger.warning(
                            'Not assembling version {} ftrackreview component {}!'.format(
                                version['id'], component['id']
                            )
                        )
                        continue
                matching_definitions = None
                for definition in loader_definitions:
                    # Matches asset type?
                    definition_asset_type_name_short = definition['asset_type']
                    if (
                        definition_asset_type_name_short
                        != version['asset']['type']['short']
                    ):
                        self._assembler_client.logger.debug(
                            '        Definition asset type {} mismatch version {}!'.format(
                                definition_asset_type_name_short,
                                version['asset']['type']['short'],
                            )
                        )
                        continue
                    definition_fragment = None
                    for d_component in definition.get('components', []):
                        component_name_effective = d_component['name']
                        if (
                            component_name_effective.lower()
                            != component['name'].lower()
                        ):
                            if self.match_component_names:
                                self._assembler_client.logger.debug(
                                    '        Definition component name {} mismatch!'.format(
                                        d_component['name']
                                    )
                                )
                                continue
                            else:
                                component_name_effective = component['name']
                        file_formats = d_component['file_formats']
                        if set(file_formats).intersection(
                            set([component_extension])
                        ):
                            # Construct fragment
                            definition_fragment = {
                                'components': [copy.deepcopy(d_component)]
                            }
                            definition_fragment['components'][0][
                                'name'
                            ] = component_name_effective
                            for key in definition:
                                if key not in [
                                    'components',
                                ]:
                                    definition_fragment[key] = copy.deepcopy(
                                        definition[key]
                                    )
                                    if key == core_constants.CONTEXTS:
                                        # Remove open context
                                        for stage in definition_fragment[key][
                                            0
                                        ]['stages']:
                                            for plugin in stage['plugins']:
                                                if not 'options' in plugin:
                                                    plugin['options'] = {}
                                                # Store version
                                                plugin['options'][
                                                    'asset_name'
                                                ] = version['asset']['name']
                                                plugin['options'][
                                                    'asset_id'
                                                ] = version['asset']['id']
                                                plugin['options'][
                                                    'version_number'
                                                ] = version['version']
                                                plugin['options'][
                                                    'version_id'
                                                ] = version['id']
                        else:
                            self._assembler_client.logger.debug(
                                '        File formats {} does not intersect with {}!'.format(
                                    file_formats,
                                    [component_extension],
                                )
                            )
                        if definition_fragment:
                            if matching_definitions is None:
                                matching_definitions = []
                            matching_definitions.append(definition_fragment)
                if matching_definitions is None:
                    if self.show_non_compatible_assets:
                        matching_definitions = []
                else:
                    self._loadable_count += 1
                if matching_definitions is not None:
                    availability = location.get_component_availability(
                        component
                    )
                    components.append(
                        (
                            component,
                            matching_definitions,
                            availability,
                        )
                    )

        return components


class AssemblerListBaseWidget(AssetListWidget):
    def __init__(self, assembler_widget, parent=None):
        self._assembler_widget = assembler_widget
        super(AssemblerListBaseWidget, self).__init__(
            self._assembler_widget.model, parent=parent
        )

    def rebuild(self):
        raise NotImplementedError()

    def get_loadable(self):
        result = []
        for widget in self.assets:
            if widget.definition is not None:
                widget.set_selected(True)
                result.append(widget)
        return result


class ComponentBaseWidget(AccordionBaseWidget):
    '''Widget representation of a minimal assembler asset representation'''

    @property
    def index(self):
        return self._index

    @property
    def options_widget(self):
        return self._options_button

    @property
    def definition(self):
        return (
            self._widget_factory.working_definition
            if self._widget_factory
            else None
        )

    @property
    def factory(self):
        return self._widget_factory

    @property
    def component_id(self):
        return self._component_id

    @property
    def session(self):
        return self._assembler_widget.session

    loader_selected = QtCore.Signal(object)

    def __init__(
        self, index, assembler_widget, event_manager, title=None, parent=None
    ):
        self._assembler_widget = assembler_widget
        super(ComponentBaseWidget, self).__init__(
            AccordionBaseWidget.SELECT_MODE_LIST,
            AccordionBaseWidget.CHECK_MODE_NONE,
            event_manager=event_manager,
            title=title,
            checked=False,
            collapsable=False,
            parent=parent,
        )
        self._version_id = None
        self._index = index
        self._adjust_height()

    def init_status_widget(self):
        self._status_widget = AssetVersionStatusWidget(bordered=False)
        self._status_widget.setMinimumWidth(60)
        # self._status_widget.setObjectName('borderless')
        return self._status_widget

    def init_options_button(self):
        self._options_button = ImporterOptionsButton(
            'O', icon.MaterialIcon('settings', color='gray')
        )
        self._options_button.setObjectName('borderless')
        self._options_button.clicked.connect(self._build_options)
        return self._options_button

    def get_thumbnail_height(self):
        raise NotImplementedError()

    def get_ident_widget(self):
        '''Widget containing name identification of asset'''
        raise NotImplementedError()

    def get_version_widget(self):
        '''Widget containing version label or combobox.'''
        raise NotImplementedError()

    def set_version(self, version_entity):
        raise NotImplementedError()

    def init_header_content(self, header_widget, collapsed):
        '''Add publish related widgets to the accordion header'''
        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_widget.setLayout(header_layout)

        upper_widget = QtWidgets.QWidget()
        upper_layout = QtWidgets.QHBoxLayout()
        upper_layout.setContentsMargins(5, 1, 1, 1)
        upper_layout.setSpacing(2)
        upper_widget.setMinimumHeight(25)
        upper_widget.setLayout(upper_layout)

        # Append thumbnail
        self.thumbnail_widget = AssetVersion(self.session)
        # self.thumbnail_widget.setScaledContents(True)

        thumb_width = (
            self.get_thumbnail_height()
        )  # int((self.get_thumbnail_height() * 4) / 3)
        self.thumbnail_widget.setMinimumWidth(thumb_width)
        self.thumbnail_widget.setMinimumHeight(self.get_thumbnail_height())
        self.thumbnail_widget.setMaximumWidth(thumb_width)
        self.thumbnail_widget.setMaximumHeight(self.get_thumbnail_height())
        upper_layout.addWidget(self.thumbnail_widget)

        upper_layout.addWidget(self.get_ident_widget())

        upper_layout.addWidget(self.init_status_widget())

        upper_layout.addWidget(QtWidgets.QLabel(), 100)

        upper_layout.addWidget(self.get_version_widget())

        # Add loader selector
        self._definition_selector = DefinitionSelector()
        self._definition_selector.setMinimumHeight(22)
        self._definition_selector.setMaximumHeight(22)
        set_property(self._definition_selector, 'chip', 'true')
        self._definition_selector.currentIndexChanged.connect(
            self._definition_selected
        )
        upper_layout.addWidget(self._definition_selector)

        # Mode selector, based on supplied DCC supported modes
        self._mode_selector = ModeSelector()
        set_property(self._mode_selector, 'chip', 'true')
        self._modes = [
            mode
            for mode in list(
                self._assembler_widget._assembler_client.modes.keys()
            )
            if mode.lower() != 'open'
        ]
        for mode in self._modes:
            if mode != 'Open':
                self._mode_selector.addItem(mode, mode)
        self._mode_selector.currentIndexChanged.connect(self._mode_selected)
        upper_layout.addWidget(self._mode_selector)

        # Options widget,initialize its factory
        upper_layout.addWidget(self.init_options_button())

        self._widget_factory = factory.ImporterWidgetFactory(
            self.event_manager,
            self._assembler_widget._assembler_client.ui_types,
        )

        header_layout.addWidget(upper_widget, 10)

        self._warning_message_widget = QtWidgets.QWidget()
        lower_layout = QtWidgets.QHBoxLayout()
        lower_layout.setContentsMargins(1, 1, 1, 1)
        lower_layout.setSpacing(1)
        self._warning_message_widget.setLayout(lower_layout)

        warning_icon_label = QtWidgets.QLabel()
        warning_icon_label.setPixmap(
            icon.MaterialIcon('warning', color='#ffba5c').pixmap(
                QtCore.QSize(16, 16)
            )
        )
        lower_layout.addWidget(warning_icon_label)
        self._warning_label = WarningLabel()
        lower_layout.addWidget(self._warning_label, 100)

        header_layout.addWidget(self._warning_message_widget)
        self._warning_message_widget.setVisible(False)

    def _definition_selected(self, index):
        '''Loader definition were selected,'''
        self._assembler_widget._assembler_client.setup_widget_factory(
            self._widget_factory,
            self._definition_selector.itemData(index),
            self._context_id,
        )
        self._set_default_mode()

    def _set_default_mode(self):
        # Set mode
        mode = self._modes[0]
        for stage in self.definition['components'][0]['stages']:
            if stage['name'] == 'importer':
                if not 'options' in stage['plugins'][0]:
                    stage['plugins'][0]['options'] = {}
                mode = stage['plugins'][0]['options'].get(
                    'load_mode', 'Import'
                )
                break
        self._mode_selector.setCurrentIndex(self._modes.index(mode))

    def _mode_selected(self, index):
        mode = self._mode_selector.itemData(index)
        # Store mode in working definition
        for stage in self.definition['components'][0]['stages']:
            if stage['name'] == 'importer':
                stage['plugins'][0]['options']['load_mode'] = mode
                break

    def _build_options(self):
        '''Build options overlay with factory'''

        self._widget_factory.build_definition_ui(
            self._options_button.main_widget
        )

        # Make sure we can save options on close
        self._options_button.overlay_container.close_btn.clicked.connect(
            self._store_options
        )

        # Show overlay
        self._options_button.on_click_callback()

    def _store_options(self):
        '''Serialize definition and store.'''
        updated_definition = self._widget_factory.to_json_object()

        self._widget_factory.set_definition(updated_definition)
        # Transfer back load mode
        self._set_default_mode()
        # Clear out overlay, not needed anymore
        clear_layout(self._options_button.main_widget.layout())

    def set_context_id(self, context_id):
        self._context_id = context_id

    def init_content(self, content_layout):
        # No content in this accordion for now
        pass

    def set_component_and_definitions(self, component, definitions):
        '''Update widget from data'''
        version_entity = component['version']
        self.set_context_id(version_entity['task']['id'])
        self._context_name = version_entity['task']['name']
        self._component_id = component['id']
        self._component_name = component['name']
        self.thumbnail_widget.load(version_entity['id'])
        self._widget_factory.version_id = version_entity['id']

        self._status_widget.set_status(version_entity['status'])

        # Deploy available loaders
        # self._definitions = definitions

        self._definition_selector.clear()
        for definition in definitions:
            self._definition_selector.addItem(definition['name'], definition)

        if len(definitions) > 0:
            # Select something
            self._definition_selector.setCurrentIndex(0)
        else:
            # No loaders, disable entire component
            self.setEnabled(False)
            if len(self._warning_label.text()) == 0:
                self.set_warning_message(
                    'No loader found compatible with this asset.'
                )

        self._asset_name_widget.setText(
            '{} '.format(version_entity['asset']['name'])
        )
        component_path = '{}{}'.format(
            component['name'], component['file_type']
        )
        self._component_filename_widget.setText(
            '- {} -'.format(component_path.replace('\\', '/').split('/')[-1])
        )
        self.set_version(version_entity)
        self.set_latest_version(version_entity['is_latest_version'])

        self.setToolTip(
            'Published by: {} {} @ {}'.format(
                version_entity['user']['first_name'],
                version_entity['user']['last_name'],
                version_entity['date'].strftime('%y-%m-%d %H:%M'),
            )
        )

    def on_collapse(self, collapsed):
        '''Not collapsable'''
        pass

    def update_input(self, message, status):
        '''Update the accordion input summary, should be overridden by child.'''
        pass

    def get_height(self):
        raise NotImplementedError()

    def _adjust_height(self):
        widget_height = self.get_height() + (
            18 if len(self._warning_label.text()) > 0 else 0
        )
        self.header.setMinimumHeight(widget_height)
        self.header.setMaximumHeight(widget_height)
        self.setMinimumHeight(widget_height)
        self.setMaximumHeight(widget_height)

    def set_warning_message(self, message):
        if len(message or '') > 0:
            self._warning_label.setText(message)
            self._warning_message_widget.setVisible(True)
        else:
            self._warning_message_widget.setVisible(False)
        self._adjust_height()


class DefinitionSelector(QtWidgets.QComboBox):
    def __init__(self):
        super(DefinitionSelector, self).__init__()
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)


class ModeSelector(QtWidgets.QComboBox):
    def __init__(self):
        super(ModeSelector, self).__init__()
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)


class ImporterOptionsButton(OptionsButton):
    def __init__(self, title, icon, parent=None):
        super(ImporterOptionsButton, self).__init__(parent=parent)
        self.name = title
        self._icon = icon

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumSize(30, 30)
        self.setMaximumSize(30, 30)
        self.setIcon(self._icon)
        self.setFlat(True)

    def build(self):
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(QtWidgets.QVBoxLayout())
        self.main_widget.layout().setAlignment(QtCore.Qt.AlignTop)
        self.main_widget.layout().setContentsMargins(5, 1, 5, 10)

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.main_widget)

        self.overlay_container = overlay.Overlay(
            self.scroll, width_percentage=0.6, height_percentage=0.9
        )
        self.overlay_container.setVisible(False)

    def post_build(self):
        pass

    def on_click_callback(self):
        main_window = get_main_framework_window_from_widget(self)
        if main_window:
            self.overlay_container.setParent(main_window)
        self.overlay_container.setVisible(True)

    def add_validator_widget(self, widget):
        self.main_widget.layout().addWidget(
            QtWidgets.QLabel('<html><strong>Validators:<strong><html>')
        )
        self.main_widget.layout().addWidget(widget)

    def add_output_widget(self, widget):
        self.main_widget.layout().addWidget(QtWidgets.QLabel(''))
        self.main_widget.layout().addWidget(
            QtWidgets.QLabel('<html><strong>Output:<strong><html>')
        )
        self.main_widget.layout().addWidget(widget)


class WarningLabel(QtWidgets.QLabel):
    def __init__(self):
        super(WarningLabel, self).__init__()
