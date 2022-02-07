# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os
import qtawesome as qta
from functools import partial

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    Context,
    AssetVersion,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetListWidget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.asset_manager import (
    AssetVersionStatusWidget,
    ComponentAndVersionWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import overlay
from ftrack_connect_pipeline_qt.utils import (
    clear_layout,
    get_main_framework_window_from_widget,
)


class ComponentListWidget(AssetListWidget):
    '''Custom asset manager list view'''

    def __init__(self, model, asset_widget_class, assembler, parent=None):
        self._assembler = assembler
        super(ComponentListWidget, self).__init__(model, parent=parent)
        self._asset_widget_class = asset_widget_class

    def rebuild(self):
        '''Add all assets(components) again from model.'''

        # TODO: Save selection state

        # Group by context
        context_components = {}
        prev_context_id = None
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)

            (component, definitions) = self.model.data(index)

            context_id = component['version']['task']['id']

            # Add a grouping element?

            if prev_context_id is None or context_id != prev_context_id:

                context_entity = self.model.session.query(
                    'select link, name, parent, parent.name from Context where id '
                    'is "{}"'.format(context_id)
                ).one()

                widget = QtWidgets.QWidget()
                widget.setLayout(QtWidgets.QHBoxLayout())
                widget.layout().setContentsMargins(1, 1, 1, 1)
                widget.layout().setSpacing(1)

                # Append thumbnail
                thumbnail_widget = Context(self.model.session)
                # self.thumbnail_widget.setScaledContents(True)

                thumbnail_widget.setMinimumWidth(50)
                thumbnail_widget.setMinimumHeight(50)
                thumbnail_widget.setMaximumWidth(50)
                thumbnail_widget.setMaximumHeight(50)
                thumbnail_widget.load(context_entity['id'])
                widget.layout().addWidget(thumbnail_widget)

                # Append a context label
                entity_info = AssemblerEntityInfo()
                entity_info.setMinimumHeight(60)
                entity_info.setMaximumHeight(60)
                entity_info.set_entity(context_entity)

                widget.layout().addWidget(entity_info)

                self.layout().addWidget(widget)

            # Append component accordion

            component_widget = self._asset_widget_class(
                index, self._assembler, self.model.event_manager
            )
            component_widget.set_component_and_definitions(
                component, definitions
            )
            self.layout().addWidget(component_widget)
            component_widget.clicked.connect(
                partial(self.asset_clicked, component_widget)
            )

        self.layout().addWidget(QtWidgets.QLabel(''), 1000)


class ComponentWidget(AccordionBaseWidget):
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

    loader_selected = QtCore.Signal(object)

    def __init__(
        self, index, assembler, event_manager, title=None, parent=None
    ):
        self._assembler = assembler
        super(ComponentWidget, self).__init__(
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
        # self._status_widget.setObjectName('borderless')
        return self._status_widget

    def init_options_button(self):
        self._options_button = OptionsButton(
            'O', qta.icon('mdi6.cog', color='gray')
        )
        self._options_button.setObjectName('borderless')
        self._options_button.clicked.connect(self._build_options)
        return self._options_button

    def init_header_content(self, header_layout, collapsed):
        '''Add publish related widgets to the accordion header'''
        header_layout.setContentsMargins(1, 1, 1, 1)
        header_layout.setSpacing(2)

        # Append thumbnail
        self.thumbnail_widget = AssetVersion(self.session)
        # self.thumbnail_widget.setScaledContents(True)

        self.thumbnail_widget.setMinimumWidth(35)
        self.thumbnail_widget.setMinimumHeight(18)
        self.thumbnail_widget.setMaximumWidth(35)
        self.thumbnail_widget.setMaximumHeight(18)
        header_layout.addWidget(self.thumbnail_widget)

        self._asset_name_widget = QtWidgets.QLabel()
        self._asset_name_widget.setObjectName('h2')
        header_layout.addWidget(self._asset_name_widget)
        self._component_and_version_header_widget = ComponentAndVersionWidget(
            True
        )
        header_layout.addWidget(self._component_and_version_header_widget)
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
            for mode in list(self._assembler.modes.keys())
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
            self.event_manager, self._assembler.ui_types
        )

    def _definition_selected(self, index):
        '''Loader definition were selected,'''
        self._assembler.setup_widget_factory(
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
        self._asset_name_widget.setText(
            '{} '.format(component['version']['asset']['name'])
        )
        self._component_and_version_header_widget.set_component_filename(
            '{}{}'.format(component['name'], component['file_type'])
        )
        self._component_and_version_header_widget.set_version(
            component['version']['version']
        )
        self._component_and_version_header_widget.set_latest_version(
            component['version']['is_latest_version']
        )
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

    def on_collapse(self, collapsed):
        '''Not collapsable'''
        pass

    def update_input(self, message, status):
        '''Update the accordion input summary, should be overridden by child.'''
        pass


class AssemblerEntityInfo(QtWidgets.QWidget):
    '''Entity path widget.'''

    path_ready = QtCore.Signal(object)

    def __init__(self, additional_widget=None, parent=None):
        '''Instantiate the entity path widget.'''
        super(AssemblerEntityInfo, self).__init__(parent=parent)

        self._additional_widget = additional_widget

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(5, 12, 2, 2)
        self.layout().setSpacing(2)

    def build(self):
        name_widget = QtWidgets.QWidget()
        name_widget.setLayout(QtWidgets.QHBoxLayout())
        name_widget.layout().setContentsMargins(1, 1, 1, 1)
        name_widget.layout().setSpacing(2)

        self._from_field = QtWidgets.QLabel('From:')
        self._from_field.setObjectName('gray')
        name_widget.layout().addWidget(self._from_field)
        if self._additional_widget:
            name_widget.layout().addWidget(self._additional_widget)
        name_widget.layout().addStretch()
        self.layout().addWidget(name_widget)

        self._path_field = QtWidgets.QLabel()
        self._path_field.setObjectName('h3')
        self.layout().addWidget(self._path_field)

        self.layout().addStretch()

    def post_build(self):
        self.path_ready.connect(self.on_path_ready)

    def set_entity(self, entity):
        '''Set the *entity* for this widget.'''
        if not entity:
            return
        parent = entity['parent']
        parents = [entity]
        while parent is not None:
            parents.append(parent)
            parent = parent['parent']
        parents.reverse()
        self.path_ready.emit(parents)

    def on_path_ready(self, parents):
        '''Set current path to *names*.'''
        self._path_field.setText(os.sep.join([p['name'] for p in parents[:]]))


class DefinitionSelector(QtWidgets.QComboBox):
    def __init__(self):
        super(DefinitionSelector, self).__init__()


class ModeSelector(QtWidgets.QComboBox):
    def __init__(self):
        super(ModeSelector, self).__init__()


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
