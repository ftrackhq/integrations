import os
import json
import time
import logging
import copy

import qtawesome as qta
from functools import partial

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
    ComponentAndVersionWidget,
)
from ftrack_connect_pipeline_qt.utils import (
    BaseThread,
    str_version,
    clear_layout,
    get_main_framework_window_from_widget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import overlay
from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)


class AssemblerBaseWidget(QtWidgets.QWidget):
    '''Base assembler dependency or browse widget'''

    @property
    def component_list(self):
        '''Return the collected object by the widget'''
        return self._component_list

    @property
    def session(self):
        return self._assembler_client.session

    def __init__(self, assembler_client, parent=None):
        super(AssemblerBaseWidget, self).__init__(parent=parent)
        self._assembler_client = assembler_client
        self._component_list = None

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.pre_build()
        self.build_header()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(2)
        self.model = AssetListModel(self._assembler_client.event_manager)

    def build(self):
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.layout().addWidget(self.scroll, 1000)

    def refresh(self):
        if self.scroll.widget():
            self.scroll.widget().deleteLater()
        self.model.reset()
        self._assembler_client.progress_widget.hide_widget()

        self._busy_widget.start()

        # Wait for context to be loaded
        self.get_context()

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

    def extract_components(self, versions, include_unloadable=False):
        '''Build a list of loadable components from the supplied *versions*'''

        # Fetch all definitions, append asset type name
        loader_definitions = []
        asset_type_name_short_mappings = {}
        for (
            definition
        ) in self._assembler_client.host_and_definition_selector.definitions:
            for package in self._assembler_client.host_connection.definitions[
                'package'
            ]:
                if package['name'] == definition.get('package'):
                    asset_type_name_short_mappings[
                        definition['name']
                    ] = package['asset_type_name']
                    loader_definitions.append(definition)
                    break

        # import json
        print(
            '@@@ loader_definitions: {}'.format(
                '\n'.join(
                    [
                        json.dumps(loader, indent=4)
                        for loader in loader_definitions
                    ]
                )
            )
        )
        # print('@@@ # loader_definitions: {}'.format(len(loader_definitions)))

        # For each version, figure out loadable components and store with
        # fragment of its possible loader definition(s)

        components = []

        # Group by context, sort by asset name
        for version in sorted(
            versions,
            key=lambda v: '{}/{}'.format(
                v['asset']['parent']['id'], v['asset']['name']
            ),
        ):
            print('@@@ Processing: {}'.format(str_version(version)))
            for component in version['components']:
                component_extension = component.get('file_type')
                print(
                    '@@@     Component: {}({})'.format(
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
                if include_unloadable:
                    matching_definitions = []
                else:
                    matching_definitions = None
                    for definition in loader_definitions:
                        # Matches asset type?
                        definition_asset_type_name_short = (
                            asset_type_name_short_mappings[definition['name']]
                        )
                        if (
                            definition_asset_type_name_short
                            != version['asset']['type']['short']
                        ):
                            print(
                                '@@@     Definition AT {} mismatch version {}!'.format(
                                    definition_asset_type_name_short,
                                    version['asset']['type']['short'],
                                )
                            )
                            continue
                        definition_fragment = None
                        for d_component in definition.get('components', []):
                            if (
                                d_component['name'].lower()
                                != component['name'].lower()
                            ):
                                print(
                                    '@@@     Definition component name {} mismatch!'.format(
                                        d_component['name']
                                    )
                                )
                                continue
                            for d_stage in d_component.get('stages', []):
                                if d_stage.get('name') == 'collector':
                                    for d_plugin in d_stage.get('plugins', []):
                                        accepted_formats = d_plugin.get(
                                            'options', {}
                                        ).get('accepted_formats')
                                        if not accepted_formats:
                                            continue
                                        if set(accepted_formats).intersection(
                                            set([component_extension])
                                        ):
                                            # Construct fragment
                                            definition_fragment = {
                                                'components': [
                                                    copy.deepcopy(d_component)
                                                ]
                                            }
                                            for key in definition:
                                                if key not in [
                                                    'components',
                                                ]:
                                                    definition_fragment[
                                                        key
                                                    ] = copy.deepcopy(
                                                        definition[key]
                                                    )
                                                    if (
                                                        key
                                                        == core_constants.CONTEXTS
                                                    ):
                                                        # Remove open context
                                                        for (
                                                            stage
                                                        ) in definition_fragment[
                                                            key
                                                        ][
                                                            0
                                                        ][
                                                            'stages'
                                                        ]:
                                                            for (
                                                                plugin
                                                            ) in stage[
                                                                'plugins'
                                                            ]:
                                                                if (
                                                                    not 'options'
                                                                    in plugin
                                                                ):
                                                                    plugin[
                                                                        'options'
                                                                    ] = {}
                                                                # Store version
                                                                plugin[
                                                                    'options'
                                                                ][
                                                                    'asset_name'
                                                                ] = version[
                                                                    'asset'
                                                                ][
                                                                    'name'
                                                                ]
                                                                plugin[
                                                                    'options'
                                                                ][
                                                                    'asset_id'
                                                                ] = version[
                                                                    'asset'
                                                                ][
                                                                    'id'
                                                                ]
                                                                plugin[
                                                                    'options'
                                                                ][
                                                                    'version_number'
                                                                ] = version[
                                                                    'version'
                                                                ]
                                                                plugin[
                                                                    'options'
                                                                ][
                                                                    'version_id'
                                                                ] = version[
                                                                    'id'
                                                                ]
                                            break
                                        else:
                                            print(
                                                '@@@     Accepted formats {} does not intersect with {}!'.format(
                                                    accepted_formats,
                                                    [component_extension],
                                                )
                                            )
                                if definition_fragment:
                                    break
                            if definition_fragment:
                                if matching_definitions is None:
                                    matching_definitions = []
                                matching_definitions.append(
                                    definition_fragment
                                )
                if matching_definitions is not None:
                    components.append((component, matching_definitions))

        return components


class AssemblerListBaseWidget(AssetListWidget):
    def __init__(self, assembler_widget, parent=None):
        self._assembler_widget = assembler_widget
        super(AssemblerListBaseWidget, self).__init__(
            self._assembler_widget.model, parent=parent
        )

    def rebuild(self):
        raise NotImplementedError()


class ComponentBaseWidget(AccordionBaseWidget):
    '''Widget representation of a minimal asset representation'''

    @property
    def index(self):
        return self._index

    @property
    def options_widget(self):
        return self._options_button

    @property
    def definition(self):
        return self._widget_factory.working_definition

    @property
    def factory(self):
        return self._widget_factory

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

    def init_status_widget(self):
        self._status_widget = AssetVersionStatusWidget()
        self._status_widget.setMinimumWidth(60)
        # self._status_widget.setObjectName('borderless')
        return self._status_widget

    def init_options_button(self):
        self._options_button = OptionsButton(
            'O', qta.icon('mdi6.cog', color='gray')
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

    def init_header_content(self, header_layout, collapsed):
        '''Add publish related widgets to the accordion header'''
        header_layout.setContentsMargins(1, 1, 1, 1)
        header_layout.setSpacing(2)

        # Append thumbnail
        self.thumbnail_widget = AssetVersion(self.session)
        # self.thumbnail_widget.setScaledContents(True)

        thumb_width = (self.get_thumbnail_height() * 16) / 9
        self.thumbnail_widget.setMinimumWidth(int(thumb_width))
        self.thumbnail_widget.setMinimumHeight(self.get_thumbnail_height())
        self.thumbnail_widget.setMaximumWidth(int(thumb_width))
        self.thumbnail_widget.setMaximumHeight(self.get_thumbnail_height())
        header_layout.addWidget(self.thumbnail_widget)

        header_layout.addWidget(self.get_ident_widget(), 100)

        header_layout.addWidget(self.get_version_widget())

        header_layout.addWidget(self.init_status_widget())

        header_layout.addStretch()

        # Add loader selector
        self._definition_selector = DefinitionSelector()
        self._definition_selector.currentIndexChanged.connect(
            self._definition_selected
        )
        header_layout.addWidget(self._definition_selector)

        # Mode selector, based on supplied DCC supported modes
        self._mode_selector = ModeSelector()
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
        header_layout.addWidget(self._mode_selector)

        # Options widget,initialize its factory
        header_layout.addWidget(self.init_options_button())

        self._widget_factory = factory.ImporterWidgetFactory(
            self.event_manager,
            self._assembler_widget._assembler_client.ui_types,
        )

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

    def init_content(self, content_layout):
        pass

    def set_component_and_definitions(self, component, definitions):
        '''Update widget from data'''
        self._context_id = component['version']['task']['id']
        self.thumbnail_widget.load(component['version']['id'])
        self._widget_factory.version_id = component['version']['id']

        self._status_widget.set_status(component['version']['status'])

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

        self._asset_name_widget.setText(
            '{} '.format(component['version']['asset']['name'])
        )
        component_path = '{}{}'.format(
            component['name'], component['file_type']
        )
        self._component_filename_widget.setText(
            '- {}'.format(component_path.replace('\\', '/').split('/')[-1])
        )

        self.set_version(component['version']['version'])
        self.set_latest_version(component['version']['is_latest_version'])

    def on_collapse(self, collapsed):
        '''Not collapsable'''
        pass

    def update_input(self, message, status):
        '''Update the accordion input summary, should be overridden by child.'''
        pass


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


class OptionsButton(QtWidgets.QPushButton):
    def __init__(self, title, icon, parent=None):
        super(OptionsButton, self).__init__(parent=parent)
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

        self.scroll = QtWidgets.QScrollArea()
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
