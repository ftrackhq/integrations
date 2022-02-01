#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import copy
import os
from functools import partial

from Qt import QtCore, QtWidgets

import qtawesome as qta

from ftrack_connect_pipeline.client import constants

from ftrack_connect_pipeline_qt.client import QtClient

from ftrack_connect_pipeline_qt.ui.utility.widget.prompt import PromptDialog
from ftrack_connect_pipeline_qt.client import factory
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    header,
    definition_selector,
    line,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    Context,
    AssetVersion,
)
from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClient,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetListModel,
    AssetListWidget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.asset_manager import (
    AssetVersionStatusWidget,
    ComponentAndVersionWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import overlay
from ftrack_connect_pipeline_qt import utils
from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import (
    MaterialIconWidget,
)


class QtAssemblerClient(QtClient):
    '''
    Base assembler widget class, based on loader but without the definition
    selector and factorized widget builder.
    '''

    client_name = 'assembler'
    definition_filter = 'loader'

    dependencies_resolved = QtCore.Signal(object)

    def __init__(self, event_manager, modes, parent=None):
        self._modes = modes
        super(QtAssemblerClient, self).__init__(event_manager, parent=parent)
        self.logger.debug('start qt assembler')

    def get_background_color(self):
        return 'ftrack'

    def pre_build(self):
        super(QtAssemblerClient, self).pre_build()

    def build(self):
        '''Build assembler widget.'''
        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)

        self._progress_widget = factory.WidgetFactory.create_progress_widget()
        self.header.id_container_layout.insertWidget(
            1, self._progress_widget.widget
        )

        self.context_selector = ContextSelector(self.session)
        self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

        self.layout().addWidget(line.Line())

        self.host_and_definition_selector = (
            definition_selector.DefinitionSelectorButtons(self.client_name)
        )
        self.host_and_definition_selector.refreshed.connect(self.refresh)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self._left_widget = QtWidgets.QWidget()
        self._left_widget.setLayout(QtWidgets.QVBoxLayout())
        self._left_widget.layout().setContentsMargins(1, 1, 1, 1)
        self._left_widget.layout().setSpacing(1)

        self._left_widget.layout().addWidget(self.host_and_definition_selector)

        self._left_widget.layout().addWidget(self.scroll, 1000)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().addStretch()
        self._run_button_no_load = LoadRunButton('ADD TO THE SCENE')
        button_widget.layout().addWidget(self._run_button_no_load)
        self.run_button = LoadRunButton('ADD AND LOAD INTO THE SCENE')
        button_widget.layout().addWidget(self.run_button)
        self._left_widget.layout().addWidget(button_widget)

        self._right_widget = QtWidgets.QWidget()
        self._right_widget.setLayout(QtWidgets.QVBoxLayout())
        self._right_widget.layout().setContentsMargins(1, 1, 1, 1)
        self._right_widget.layout().setSpacing(1)

        # Create and add the asset manager client
        self._asset_manager = QtAssetManagerClient(
            self.event_manager, slave=True
        )
        self._right_widget.layout().addWidget(self._asset_manager)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().addStretch()
        self._remove_button = RemoveButton('REMOVE FROM SCENE')
        button_widget.layout().addWidget(self._remove_button)
        self._right_widget.layout().addWidget(button_widget)

        # Create a splitter and add to client
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self._left_widget)
        self.splitter.addWidget(self._right_widget)
        self.layout().addWidget(self.splitter, 100)
        self.splitter.setSizes([500, 300])

    def post_build(self):
        super(QtAssemblerClient, self).post_build()
        self.dependencies_resolved.connect(self.on_dependencies_resolved)

    def change_host(self, host_connection):
        super(QtAssemblerClient, self).change_host(host_connection)
        # Feed the host to the asset manager
        self._asset_manager.change_host(host_connection)

    def on_dependencies_resolved_async(self, result):
        self.dependencies_resolved.emit(result)

    def _resolve_dependencies(self, context_id):
        try:
            return self._asset_manager.resolve_dependencies(
                context_id, self.on_dependencies_resolved_async
            )
        except:
            import traceback

            print(traceback.format_exc())

    def refresh(self):
        super(QtAssemblerClient, self).refresh()
        # Clear out current deps
        if self.scroll.widget():
            self.scroll.widget().deleteLater()
        # Add spinner
        _busy_v_container = QtWidgets.QWidget()
        _busy_v_container.setLayout(QtWidgets.QVBoxLayout())
        _busy_h_container = QtWidgets.QWidget()
        _busy_h_container.setLayout(QtWidgets.QHBoxLayout())
        self._busy_widget = BusyIndicator()
        self._busy_widget.setMaximumSize(QtCore.QSize(30, 30))
        _busy_h_container.layout().addWidget(self._busy_widget)
        _busy_v_container.layout().addWidget(_busy_h_container)
        self.scroll.setWidget(_busy_v_container)
        self._busy_widget.start()

        # Resolve version this context is depending on in separate thread
        thread = BaseThread(
            name='resolve_dependencies_thread',
            target=self._resolve_dependencies,
            target_args=[self.context_selector.context_id],
        )
        thread.start()

    def str_version(self, v):
        return '{}/{}({})'.format(
            '/'.join(
                ['{}'.format(link['name']) for link in v['task']['link']]
            ),
            v['asset']['name'],
            v['asset']['type']['name'],
            v['id'],
        )

    def on_dependencies_resolved(self, result):
        self._busy_widget.stop()

        versions = None
        user_message = None
        if isinstance(result, dict):
            # Versions without a user message
            versions = result['versions']
        else:
            if isinstance(result, tuple):
                # With user message?
                if isinstance(result[0], dict):
                    versions = result[0].get('versions') or []
                if isinstance(result[1], dict):
                    user_data = result[1]
                    if 'message' in user_data:
                        user_message = user_data['message']
        if user_message:
            self._progress_widget.set_status(
                constants.WARNING_STATUS, user_message
            )

        self.scroll.widget().deleteLater()

        if len(versions or []) == 0:
            if user_message is None:
                self._progress_widget.set_status(
                    constants.WARNING_STATUS, 'No dependencies found!'
                )
            return

        # Process versions, filter against
        print(
            '@@@ resolved versions: {}'.format(
                ','.join([self.str_version(v) for v in versions])
            )
        )

        loader_definitions = self.host_and_definition_selector.definitions

        # print('@@@ loader_definitions: {}'.format('\n'.join([json.dumps(loader, indent=4) for loader in loader_definitions])))
        print('@@@ # loader_definitions: {}'.format(len(loader_definitions)))

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
            for component in version['components']:
                component_extension = component.get('file_type')
                if not component_extension:
                    self.logger.warning(
                        'Could not assemble version {} component {}; missing file type!'.format(
                            version['id'], component['id']
                        )
                    )
                    continue
                matching_definitions = None
                for definition in loader_definitions:
                    definition_fragment = None
                    for d_component in definition.get('components', []):
                        if (
                            d_component['name'].lower()
                            != component['name'].lower()
                        ):
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
                                                'contexts',
                                                'components',
                                            ]:
                                                definition_fragment[
                                                    key
                                                ] = copy.deepcopy(
                                                    definition[key]
                                                )
                                        break
                            if definition_fragment:
                                break
                        if definition_fragment:
                            break
                    if definition_fragment:
                        if matching_definitions is None:
                            matching_definitions = []
                        matching_definitions.append(definition_fragment)
                if matching_definitions is not None:
                    components.append((component, matching_definitions))

        if len(components) == 0:
            self._progress_widget.set_status(
                constants.WARNING_STATUS, 'No loadable dependencies found!'
            )
            return

        # Create component list
        self._component_list = ComponentListWidget(
            AssetListModel(self.event_manager),
            ComponentWidget,
            self._modes,
            self._asset_manager.ui_types,
        )
        # self._asset_list.setStyleSheet('background-color: blue;')

        self.scroll.setWidget(self._component_list)

        # Will trigger list to be rebuilt.
        self._component_list.model.insertRows(0, components)

    def run(self, load=True):
        '''Function called when click the run button'''
        # Run loader on a batch of components
        pass

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.RightButton:
            self._component_list.clear_selection()
        return super(QtAssemblerClient, self).mousePressEvent(event)


class LoadRunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(LoadRunButton, self).__init__(label, parent=parent)
        self.setIcon(MaterialIconWidget('check'))


class RemoveButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(RemoveButton, self).__init__(label, parent=parent)
        self.setIcon(MaterialIconWidget('close'))


class ComponentListWidget(AssetListWidget):
    '''Custom asset manager list view'''

    def __init__(
        self, model, asset_widget_class, modes, ui_types, parent=None
    ):
        super(ComponentListWidget, self).__init__(model, parent=parent)
        self._asset_widget_class = asset_widget_class
        self._modes = modes
        self._ui_types = ui_types

    def rebuild(self):
        '''Add all assets(components) again from model.'''

        # TODO: Save selection state

        # Group by context
        context_components = {}
        prev_context_id = None
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)

            (component, definitions) = self.model.data(index)

            # print('@@@ got loadable component: {}({}), definitions: {}'.format(component['name'], component['id'],
            #   '\n'.join(
            #       [json.dumps(loader, indent=4) for
            #        loader in definitions])))

            context_id = component['version']['asset']['parent']['id']

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
                index, self._modes, self._ui_types, self.model.event_manager
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

    loader_selected = QtCore.Signal(object)

    def __init__(
        self, index, modes, ui_types, event_manager, title=None, parent=None
    ):
        self._modes = modes
        self._ui_types = ui_types
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
        self._loader_selector = LoaderSelector()
        self._loader_selector.currentIndexChanged.connect(
            self._loader_selected
        )
        header_layout.addWidget(self._loader_selector)

        # Mode selector, based on supplied DCC supported modes
        self._mode_selector = ModeSelector()
        for mode in self._modes:
            self._mode_selector.addItem(mode, mode)
        header_layout.addWidget(self._mode_selector)

        # Options widget,initialize its factory
        header_layout.addWidget(self.init_options_button())

        self.widget_factory = factory.ImporterWidgetFactory(
            self.event_manager, self._ui_types
        )

    def _loader_selected(self, index):
        self.widget_factory.set_definition(
            self._loader_selector.itemData(index)
        )

    def _build_options(self):
        # Clear out overlay
        for i in range(self._options_button.main_widget.layout().count()):
            widget = (
                self._options_button.main_widget.layout().itemAt(i).widget()
            )
            widget.setParent(None)
            widget.deleteLater()
        # Build overlay with factory

        # Show overlay
        self._options_button.on_click_callback()

    def init_content(self, content_layout):
        pass

    def set_component_and_definitions(self, component, definitions):
        '''Update widget from data'''
        self.thumbnail_widget.load(component['version']['id'])

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

        self._loader_selector.clear()
        for definition in definitions:
            self._loader_selector.addItem(definition['name'], definition)

        if len(definitions) > 0:
            # Select something
            self._loader_selector.setCurrentIndex(0)
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
        self.layout().setContentsMargins(2, 12, 2, 2)
        self.layout().setSpacing(2)

    def build(self):
        name_widget = QtWidgets.QWidget()
        name_widget.setLayout(QtWidgets.QHBoxLayout())
        name_widget.layout().setContentsMargins(2, 1, 2, 1)
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


class LoaderSelector(QtWidgets.QComboBox):
    def __init__(self):
        super(LoaderSelector, self).__init__()


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
        self.overlay_container = overlay.Overlay(self.main_widget)
        self.overlay_container.setVisible(False)

    def post_build(self):
        # self.clicked.connect(self.on_click_callback)
        pass

    def on_click_callback(self):
        main_window = utils.get_main_framework_window_from_widget(self)
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
