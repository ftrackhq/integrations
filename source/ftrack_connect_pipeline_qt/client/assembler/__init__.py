#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import copy
import json
from functools import partial

from Qt import QtCore, QtWidgets

import qtawesome as qta

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.client import constants

from ftrack_connect_pipeline_qt.client import QtClient

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
from ftrack_connect_pipeline_qt.utils import BaseThread, str_version

from ftrack_connect_pipeline_qt.client.asset_manager import (
    QtAssetManagerClient,
)

from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetListModel,
)
from ftrack_connect_pipeline_qt.ui.assembler.assembler import (
    ComponentListWidget,
    ComponentWidget,
)


class QtAssemblerClient(QtClient):
    '''
    Base assembler widget class, based on loader but without the definition
    selector and factorized widget builder.
    '''

    client_name = 'assembler'
    definition_filter = 'loader'
    hard_refresh = True  # Flag telling assembler that next refresh should include dependency resolve

    dependencies_resolved = QtCore.Signal(object)

    def __init__(self, event_manager, modes, parent=None):
        self.modes = modes
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

        self._progress_widget = factory.WidgetFactory.create_progress_widget(
            self.client_name
        )
        self.header.id_container_layout.insertWidget(
            1, self._progress_widget.widget
        )

        self.context_selector = ContextSelector(self.session)
        self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

        self.layout().addWidget(line.Line())

        self.host_and_definition_selector = (
            definition_selector.DefinitionSelectorButtons(self.client_name)
        )
        self.host_and_definition_selector.refreshed.connect(
            partial(self.refresh, True)
        )

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self._left_widget = QtWidgets.QWidget()
        self._left_widget.setLayout(QtWidgets.QVBoxLayout())
        self._left_widget.layout().setContentsMargins(1, 1, 1, 1)
        self._left_widget.layout().setSpacing(1)

        self._left_widget.layout().addWidget(self.host_and_definition_selector)

        self._left_widget.layout().addWidget(self.scroll, 1000)

        self._component_list = None

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
        self.asset_manager = QtAssetManagerClient(
            self.event_manager, assembler=True
        )
        self._right_widget.layout().addWidget(self.asset_manager, 100)

        # Create a splitter and add to client
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self._left_widget)
        self.splitter.addWidget(self._right_widget)
        self.layout().addWidget(self.splitter, 100)
        self.splitter.setSizes([500, 300])

    def post_build(self):
        super(QtAssemblerClient, self).post_build()
        self.dependencies_resolved.connect(self.on_dependencies_resolved)
        self.asset_manager.assets_discovered.connect(self._assets_discovered)

    def change_host(self, host_connection):
        super(QtAssemblerClient, self).change_host(host_connection)
        # Feed the host to the asset manager
        self.asset_manager.change_host(host_connection)

    def change_definition(self, schema, definition, component_names_filter):
        '''Not valid for assembler'''
        pass

    def _assets_discovered(self):
        '''The assets in AM has been discovered, refresh at our end.'''
        if self.hard_refresh:
            self.refresh()

    def on_dependencies_resolved_async(self, result):
        self.dependencies_resolved.emit(result)

    def _resolve_dependencies(self, context_id):
        try:
            return self.asset_manager.resolve_dependencies(
                context_id, self.on_dependencies_resolved_async
            )
        except:
            import traceback

            print(traceback.format_exc())

    def refresh(self, force_hard_refresh=False):
        super(QtAssemblerClient, self).refresh()
        if force_hard_refresh:
            self.hard_refresh = True
        if self.hard_refresh:
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
            self.hard_refresh = False

    def reset(self):
        '''Assembler is shown again after being hidden.'''
        self.refresh(True)
        self._progress_widget.hide_widget()
        self._progress_widget.clear_components()

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
                ','.join([str_version(v) for v in versions])
            )
        )

        # Fetch all definitions, append asset type name
        loader_definitions = []
        asset_type_name_short_mappings = {}
        for definition in self.host_and_definition_selector.definitions:
            for package in self.host_connection.definitions['package']:
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
                                                        for plugin in stage[
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
                                                            plugin['options'][
                                                                'asset_name'
                                                            ] = version[
                                                                'asset'
                                                            ][
                                                                'name'
                                                            ]
                                                            plugin['options'][
                                                                'asset_id'
                                                            ] = version[
                                                                'asset'
                                                            ][
                                                                'id'
                                                            ]
                                                            plugin['options'][
                                                                'version_number'
                                                            ] = version[
                                                                'version'
                                                            ]
                                                            plugin['options'][
                                                                'version_id'
                                                            ] = version['id']
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
            AssetListModel(self.event_manager), ComponentWidget, self
        )
        # self._asset_list.setStyleSheet('background-color: blue;')

        self.scroll.setWidget(self._component_list)

        # Will trigger list to be rebuilt.
        self._component_list.model.insertRows(0, components)

    def setup_widget_factory(self, widget_factory, definition, context_id):
        print(
            '@@@ definition({},{},{})'.format(
                widget_factory, json.dumps(definition, indent=4), context_id
            )
        )
        widget_factory.set_definition(definition)
        current_package = self.get_current_package(definition)
        widget_factory.set_context(
            context_id, current_package['asset_type_name']
        )
        widget_factory.host_connection = self._host_connection
        widget_factory.set_definition_type(definition['type'])
        widget_factory.set_package(current_package)

    def run(self, delayed_load=False):
        '''Function called when click the run button'''
        # Load batch of components, any selected
        component_widgets = self._component_list.selection(
            empty_returns_all=True, as_widgets=True
        )
        if len(component_widgets) > 0:
            # Each component contains a definition ready to run and a factory,
            # run them one by one. Start by preparing progress widget
            self._progress_widget.prepare_add_components()
            self._progress_widget.set_status(
                constants.RUNNING_STATUS, 'Initializing...'
            )
            for component_widget in component_widgets:
                component = self._component_list.model.data(
                    component_widget.index
                )[0]
                factory = component_widget.factory
                factory.progress_widget = (
                    self._progress_widget
                )  # Have factory update main progress widget
                self._progress_widget.add_version(component['version'])
                factory.build_progress_ui(component)
            self._progress_widget.components_added()

            self._progress_widget.show_widget()
            failed = 0
            for component_widget in component_widgets:
                # Prepare progress widget
                component = self._component_list.model.data(
                    component_widget.index
                )[0]
                self._progress_widget.set_status(
                    constants.RUNNING_STATUS,
                    'Loading {}...'.format(str_version(component['version'])),
                )
                definition = component_widget.definition
                factory = component_widget.factory
                factory.listen_widget_updates()

                engine_type = definition['_config']['engine_type']
                import json

                print(
                    '@@@ Running: {}'.format(json.dumps(definition, indent=4))
                )

                self.run_definition(definition, engine_type, delayed_load)
                # Did it go well?
                if factory.has_error:
                    failed += 1
                component_widget.factory.end_widget_updates()

            succeeded = len(component_widgets) - failed
            if succeeded > 0:
                if failed == 0:
                    self._progress_widget.set_status(
                        constants.SUCCESS_STATUS,
                        'Successfully {} {}/{} asset{}!'.format(
                            'loaded' if not delayed_load else 'tracked',
                            succeeded,
                            len(component_widgets),
                            's' if len(component_widgets) > 1 else '',
                        ),
                    )
                else:
                    self._progress_widget.set_status(
                        constants.WARNING_STATUS,
                        'Successfully {} {}/{} asset{}, {} failed - check logs for more information!'.format(
                            'loaded' if not delayed_load else 'tracked',
                            succeeded,
                            len(component_widgets),
                            's' if len(component_widgets) > 1 else '',
                            failed,
                        ),
                    )
                self.asset_manager.refresh_ui()
            else:
                self._progress_widget.set_status(
                    constants.ERROR_STATUS,
                    'Could not {} asset{} - check logs for more information!'.format(
                        'loaded' if not delayed_load else 'tracked',
                        's' if len(component_widgets) > 1 else '',
                    ),
                )

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.RightButton and self._component_list:
            self._component_list.clear_selection()
        return super(QtAssemblerClient, self).mousePressEvent(event)


class LoadRunButton(QtWidgets.QPushButton):
    def __init__(self, label, parent=None):
        super(LoadRunButton, self).__init__(label, parent=parent)
        self.setIcon(qta.icon('mdi6.check', color='#5EAA8D'))
