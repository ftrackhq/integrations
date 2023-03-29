# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging
import copy
import os

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.client import constants
from ftrack_connect_pipeline.constants import plugin
from ftrack_connect_pipeline.definition.definition_object import (
    DefinitionObject,
    DefinitionList,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetListWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    AssetVersion,
)
from ftrack_connect_pipeline_qt.ui.factory.assembler import (
    AssemblerWidgetFactory,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager import (
    AssetVersionStatusWidget,
)
from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline_qt.utils import (
    set_property,
    clear_layout,
    get_main_framework_window_from_widget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import (
    VersionComboBox,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.ui.utility.widget.button import OptionsButton
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    icon,
    overlay,
    scroll_area,
)


class AssemblerBaseWidget(QtWidgets.QWidget):
    '''Base assembler dependency or browse widget, resides within tabbed pane'''

    stopBusyIndicator = QtCore.Signal()
    listWidgetCreated = QtCore.Signal(object)
    loadError = QtCore.Signal(
        object
    )  # Emitted if a critical error occurs during load

    @property
    def component_list(self):
        '''Return the collected object by the widget'''
        return self._component_list

    @property
    def loadable_count(self):
        '''Return the number of loadable components'''
        return self._loadable_count

    @property
    def match_component_names(self):
        '''Return True if component should be matched by name'''
        return self._rb_match_component_name.isChecked()

    @property
    def show_non_compatible_assets(self):
        '''Return True if non compatible assets should be shown'''
        return self._cb_show_non_compatible.isChecked()

    @property
    def client(self):
        '''Return the client'''
        return self._client

    @property
    def session(self):
        return self._client.session

    def __init__(self, client):
        '''
        :param client: The assembler/loader client
        :param parent: The parent dialog widget
        '''
        super(AssemblerBaseWidget, self).__init__(parent=client)
        self._client = client
        self._component_list = None
        self._loadable_count = -1

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Create the model'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(1, 0, 1, 0)
        self.layout().setSpacing(0)
        self.model = AssetListModel(self.client.event_manager)

    def _build_header(self):
        '''Create assembler widget header'''
        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(QtWidgets.QVBoxLayout())
        header_widget.layout().setContentsMargins(4, 4, 4, 4)
        header_widget.layout().setSpacing(0)

        top_toolbar_widget = QtWidgets.QWidget()
        top_toolbar_widget.setLayout(QtWidgets.QHBoxLayout())
        top_toolbar_widget.layout().setContentsMargins(4, 4, 4, 2)
        top_toolbar_widget.layout().setSpacing(4)

        top_widget = self._get_header_widget()
        top_toolbar_widget.layout().addWidget(top_widget, 10)
        top_widget.setMinimumHeight(27)

        header_widget.layout().addWidget(top_toolbar_widget)

        # Add toolbar

        bottom_toolbar_widget = QtWidgets.QWidget()
        bottom_toolbar_widget.setLayout(QtWidgets.QHBoxLayout())
        bottom_toolbar_widget.layout().setContentsMargins(4, 0, 4, 1)
        bottom_toolbar_widget.layout().setSpacing(6)

        match_label = QtWidgets.QLabel('Match: ')
        match_label.setObjectName('gray-dark')
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
        bottom_toolbar_widget.layout().addWidget(self._cb_show_non_compatible)

        bottom_toolbar_widget.layout().addWidget(QtWidgets.QLabel(), 10)

        self._label_info = QtWidgets.QLabel('')
        self._label_info.setObjectName('gray')
        bottom_toolbar_widget.layout().addWidget(self._label_info)

        self._search = Search()
        bottom_toolbar_widget.layout().addWidget(self._search)

        self._rebuild_button = CircularButton('sync')
        bottom_toolbar_widget.layout().addWidget(self._rebuild_button)

        self._busy_widget = BusyIndicator(start=False)
        self._busy_widget.setMinimumSize(QtCore.QSize(16, 16))
        bottom_toolbar_widget.layout().addWidget(self._busy_widget)
        self._busy_widget.setVisible(False)

        header_widget.layout().addWidget(bottom_toolbar_widget)

        return header_widget

    def _get_header_widget(self):
        '''To be overridden by child'''
        raise NotImplementedError()

    def build(self):
        self.layout().addWidget(self._build_header())

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setStyle(QtWidgets.QStyleFactory.create("plastique"))

        self.layout().addWidget(self.scroll, 1000)

    def rebuild(self, reset=True):
        '''Prepare rebuild of the widget. If *reset* is False, assume chunked
        fetch to continue were left off'''
        if self.client.context_id is None:
            self.logger.warning(
                'No context set, cannut rebuild assembler widget'
            )
            return
        if reset:
            # Check if there is any loader definitions
            if len(self.client.definition_selector.definitions or []) == 0:
                self.client.progress_widget.set_status(
                    constants.WARNING_STATUS,
                    'No loader definitions are available, please check pipeline configuration!',
                )
                return False

            self.model.reset()
            self._loadable_count = 0

        self.update()
        self._label_info.setText('Fetching, please stand by...')
        self.client.progress_widget.hide_widget()

        self._busy_widget.start()
        self._rebuild_button.setVisible(False)
        self._busy_widget.setVisible(True)

        return True

    def reset(self):
        '''Called when widget is being redisplayed, to be overridden by child.'''
        pass

    def post_build(self):
        self._cb_show_non_compatible.clicked.connect(self.rebuild)
        if self.client.assembler_match_extension:
            self._rb_match_extension.setChecked(True)
        else:
            self._rb_match_component_name.setChecked(True)
        self._rb_match_component_name.clicked.connect(self.rebuild)
        self._rb_match_extension.clicked.connect(self.rebuild)
        self.stopBusyIndicator.connect(self._stop_busy_indicator)
        self.loadError.connect(self._on_load_error)

    def update(self):
        '''Update widget inputs'''
        self._rb_match_component_name.setEnabled(
            not self._cb_show_non_compatible.isChecked()
        )
        self._rb_match_extension.setEnabled(
            not self._cb_show_non_compatible.isChecked()
        )

    def _stop_busy_indicator(self):
        '''Stop and hide the spinner, bring back refresh button'''
        self._busy_widget.stop()
        self._busy_widget.setVisible(False)
        self._rebuild_button.setVisible(True)

    def _on_load_error(self, error_message):
        '''Act upon a load error - set progress widget status and display *error_message*'''
        self.client.progress_widget.set_status(
            constants.WARNING_STATUS, error_message
        )

    def mousePressEvent(self, event):
        '''Make sure to clear selection when not right clicking an item'''
        if event.button() != QtCore.Qt.RightButton and self._component_list:
            self._component_list.clear_selection()
        return super(AssemblerBaseWidget, self).mousePressEvent(event)

    def extract_components(self, versions):
        '''Build a list of loadable components from the supplied *versions*'''

        # Fetch all definitions, append asset type name
        loader_definitions = self.client.definition_selector.definitions

        # import json
        self.client.logger.debug(
            'Available loader definitions: {}'.format(
                '\n'.join(
                    [loader.to_json(indent=4) for loader in loader_definitions]
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
            self.client.logger.debug(
                'Processing version: {}'.format(
                    str_version(version, with_id=True)
                )
            )

            for component in version['components']:
                component_extension = component.get('file_type')
                self.client.logger.debug(
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
                        core_constants.FTRACKREVIEW_COMPONENT_NAME
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
                        self.client.logger.debug(
                            '        Definition asset type {} mismatch version {}!'.format(
                                definition_asset_type_name_short,
                                version['asset']['type']['short'],
                            )
                        )
                        continue
                    definition_fragment = None
                    for d_component in definition.get_all(
                        type=core_constants.COMPONENT
                    ):
                        component_name_effective = d_component['name']
                        if (
                            component_name_effective.lower()
                            != component['name'].lower()
                        ):
                            if self.match_component_names:
                                self.client.logger.debug(
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
                            # Construct definition fragment
                            definition_fragment = DefinitionObject({})
                            for key in definition:
                                if key == core_constants.COMPONENTS:
                                    # Have that as the only component
                                    definition_fragment[key] = DefinitionList(
                                        [
                                            DefinitionObject(
                                                d_component.to_dict()
                                            )
                                        ]
                                    )
                                    component_fragment = (
                                        definition_fragment.get_first(
                                            type=core_constants.COMPONENT
                                        )
                                    )
                                    # Make sure component name align
                                    component_fragment[
                                        'name'
                                    ] = component_name_effective
                                    # It can be disabled, enable it
                                    component_fragment['enabled'] = True
                                else:
                                    # Copy the category
                                    definition_fragment[key] = copy.deepcopy(
                                        definition[key]
                                    )
                                    if key != core_constants.CONTEXTS:
                                        continue
                                    # Inject context ident
                                    for plugin in definition_fragment[
                                        key
                                    ].get_all(
                                        type=core_constants.CONTEXT,
                                        category=core_constants.PLUGIN,
                                    ):
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
                            self.client.logger.debug(
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
                    self.logger.info(
                        'Assembled version {0} component {1}({2}) for import'.format(
                            version['id'], component['name'], component['id']
                        )
                    )

        return components


class AssemblerListBaseWidget(AssetListWidget):
    '''Base for asset lists within the assembler'''

    def __init__(self, assembler_widget, parent=None):
        self._assembler_widget = assembler_widget
        super(AssemblerListBaseWidget, self).__init__(
            self._assembler_widget.model, parent=parent
        )

    def rebuild(self):
        '''Rebuild the list widget, must be implemented by child'''
        raise NotImplementedError()

    def get_loadable(self):
        '''Return a list of all loadable assets regardless of selection'''
        result = []
        for widget in self.assets:
            if widget.definition is not None:
                widget.set_selected(True)
                result.append(widget)
        return result


class ComponentBaseWidget(AccordionBaseWidget):
    '''Base widget representation of an asset within the assembler'''

    @property
    def index(self):
        '''Return the index this asset has in list'''
        return self._index

    @property
    def options_widget(self):
        '''Return the widget representing options'''
        return self._options_button

    @property
    def definition(self):
        '''Return the currently selected definition to use for loading'''
        return (
            self._widget_factory.definition if self._widget_factory else None
        )

    @property
    def factory(self):
        '''Return the factory to use for building options and loader serialize'''
        return self._widget_factory

    @property
    def component_id(self):
        '''Return the id of this asset (component)'''
        return self._component_id

    @property
    def context_id(self):
        '''Return the context id of this asset'''
        return self._context_id

    @context_id.setter
    def context_id(self, value):
        '''Set the context id of this asset'''
        self._context_id = value

    @property
    def warning_message(self):
        '''Return the warning message'''
        return self._warning_label.text()

    @warning_message.setter
    def warning_message(self, value):
        '''Set the warning message and adjust height'''
        if len(value or '') > 0:
            self._warning_label.setText(value)
            self._warning_message_widget.setVisible(True)
        else:
            self._warning_message_widget.setVisible(False)
        self._adjust_height()

    @property
    def session(self):
        return self._assembler_widget.session

    def __init__(self, index, assembler_widget, event_manager, parent=None):
        '''
        Instantiate the asset widget

        :param index: index of this asset has in list
        :param assembler_widget: :class:`~ftrack_connect_pipeline_qt.ui.assembler.base.AssemblerBaseWidget` instance
        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param parent: the parent dialog or frame
        '''
        self._assembler_widget = assembler_widget
        super(ComponentBaseWidget, self).__init__(
            AccordionBaseWidget.SELECT_MODE_LIST,
            AccordionBaseWidget.CHECK_MODE_NONE,
            event_manager=event_manager,
            checked=False,
            collapsable=False,
            parent=parent,
        )
        self._version_id = None
        self._index = index
        self._adjust_height()

    def init_status_widget(self):
        '''Build the asset status widget.'''
        self._status_widget = AssetVersionStatusWidget(bordered=False)
        self._status_widget.setMinimumWidth(60)
        return self._status_widget

    def init_options_button(self):
        '''Create the options button and connect it to option build function'''
        self._options_button = ImporterOptionsButton(
            'O', icon.MaterialIcon('settings', color='gray')
        )
        self._options_button.setObjectName('borderless')
        self._options_button.clicked.connect(self._build_options)
        return self._options_button

    def get_thumbnail_height(self):
        '''Return the height of the thumbnail, must be implemented by child'''
        raise NotImplementedError()

    def get_ident_widget(self):
        '''Widget containing name identification of asset, must be implemented by child'''
        raise NotImplementedError()

    def get_version_widget(self):
        '''Widget containing version label or combobox, must be implemented by child'''
        raise NotImplementedError()

    def set_version(self, version_entity):
        '''Set the current *version_entity*, must be implemented by child'''
        raise NotImplementedError()

    def set_latest_version(self, is_latest_version):
        '''Set the current *is_latest_version*, must be implemented by child'''
        raise NotImplementedError()

    def init_header_content(self, header_widget, collapsed):
        '''Build all widgets to put in the accordion header'''
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
            for mode in list(self._assembler_widget.client.modes.keys())
            if mode.lower() != 'open'
        ]
        for mode in self._modes:
            if mode != 'Open':
                self._mode_selector.addItem(mode, mode)
        self._mode_selector.currentIndexChanged.connect(self._mode_selected)
        upper_layout.addWidget(self._mode_selector)

        # Options widget,initialize its factory
        upper_layout.addWidget(self.init_options_button())

        self._widget_factory = AssemblerWidgetFactory(
            self.event_manager, self._assembler_widget.client.ui_types
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
        self._assembler_widget.client.setup_widget_factory(
            self._widget_factory,
            self._definition_selector.itemData(index),
            self.context_id,
        )
        self._set_default_mode()

    def _set_default_mode(self):
        '''Find out from which is the default load mode and set it'''
        mode = self._modes[0]
        plugin = self.definition.get_first(
            category=core_constants.PLUGIN,
            type=core_constants.plugin._PLUGIN_IMPORTER_TYPE,
        )
        if not 'options' in plugin:
            plugin['options'] = {}
        mode = plugin['options'].get('load_mode', mode)
        self._mode_selector.setCurrentIndex(self._modes.index(mode))

    def _mode_selected(self, index):
        '''Load mode has been selected, store in definition'''
        mode = self._mode_selector.itemData(index)
        # Store mode in working definition
        plugin = self.definition.get_first(
            category=core_constants.PLUGIN,
            type=core_constants.plugin._PLUGIN_IMPORTER_TYPE,
        )
        plugin['options']['load_mode'] = mode

    def _build_options(self):
        '''Build options overlay with factory'''
        self._widget_factory.build(self.options_widget.main_widget)
        # Make sure we can save options on close
        self.options_widget.overlay_container.close_btn.clicked.connect(
            self._store_options
        )
        # Show overlay
        self.options_widget.show_overlay()

    def _store_options(self):
        '''Serialize definition and store'''
        updated_definition = self._widget_factory.to_json_object()

        self._widget_factory.set_definition(updated_definition)
        # Transfer back load mode
        self._set_default_mode()
        # Clear out overlay, not needed anymore
        clear_layout(self.options_widget.main_widget.layout())

    def init_content(self, content_layout):
        '''No content in this accordion for now'''
        pass

    def set_component_and_definitions(self, component, definitions):
        '''Update widget from data'''
        version_entity = component['version']
        self.context_id = version_entity['task']['id']
        self._context_name = version_entity['task']['name']
        self._component_id = component['id']
        self._component_name = component['name']
        self.thumbnail_widget.load(version_entity['id'])
        self._widget_factory.batch_id = version_entity['id']

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
            if len(self.warning_message) == 0:
                self.warning_message = (
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
            'Published by: {} {} @ {}\nComment: {}'.format(
                version_entity['user']['first_name'],
                version_entity['user']['last_name'],
                version_entity['date'].strftime('%y-%m-%d %H:%M'),
                version_entity['comment'],
            )
        )

    def on_collapse(self, collapsed):
        '''Not collapsable'''
        pass

    def get_height(self):
        '''Return the height of the widget in pixels, should be overridden by child'''
        raise NotImplementedError()

    def _adjust_height(self):
        '''Align the height with warning label'''
        widget_height = self.get_height() + (
            18 if len(self.warning_message) > 0 else 0
        )
        self.header.setMinimumHeight(widget_height)
        self.header.setMaximumHeight(widget_height)
        self.setMinimumHeight(widget_height)
        self.setMaximumHeight(widget_height)


class DefinitionSelector(QtWidgets.QComboBox):
    '''Combobox for selecting loader definition'''

    def __init__(self):
        super(DefinitionSelector, self).__init__()
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)


class ModeSelector(QtWidgets.QComboBox):
    '''Combobox for selecting the load mode'''

    def __init__(self):
        super(ModeSelector, self).__init__()
        self.setMinimumHeight(22)
        self.setMaximumHeight(22)


class ImporterOptionsButton(OptionsButton):
    '''Create loader options button with its overlay'''

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

    def show_overlay(self):
        '''Bring up options'''
        main_window = get_main_framework_window_from_widget(self)
        if main_window:
            self.overlay_container.setParent(main_window)
        self.overlay_container.setVisible(True)


class AssemblerEntityInfo(QtWidgets.QWidget):
    '''Entity info widget for the assembler.'''

    pathReady = QtCore.Signal(object)

    @property
    def entity(self):
        return self._entity

    @entity.setter
    def entity(self, value):
        '''Set the entity for this widget to *value*'''
        if not value:
            return
        self._entity = value
        parent = value['parent']
        parents = [value]
        while parent is not None:
            parents.append(parent)
            parent = parent['parent']
        parents.reverse()
        self.pathReady.emit(parents)

    def __init__(self, parent=None):
        '''Instantiate the entity path widget.'''
        super(AssemblerEntityInfo, self).__init__(parent=parent)

        self._entity = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(5, 2, 2, 2)
        self.layout().setSpacing(2)

    def build(self):
        self._from_field = QtWidgets.QLabel('Dependency from')
        self._from_field.setObjectName('gray-dark')
        self.layout().addWidget(self._from_field)

        self._path_field = QtWidgets.QLabel()
        self.layout().addWidget(self._path_field)

        self.layout().addStretch()

    def post_build(self):
        self.pathReady.connect(self.on_path_ready)

    def on_path_ready(self, parents):
        '''Set current path to *names*.'''
        self._path_field.setText(os.sep.join([p['name'] for p in parents[:]]))


class AssemblerVersionComboBox(VersionComboBox):
    def __init__(self, session, parent=None):
        super(AssemblerVersionComboBox, self).__init__(session, parent=parent)

    def _add_version(self, version_and_compatible_tuple):
        '''Override'''
        version, is_compatible = version_and_compatible_tuple
        self.addItem(
            str("v{}".format(version['version'])), version_and_compatible_tuple
        )


class WarningLabel(QtWidgets.QLabel):
    def __init__(self):
        super(WarningLabel, self).__init__()
