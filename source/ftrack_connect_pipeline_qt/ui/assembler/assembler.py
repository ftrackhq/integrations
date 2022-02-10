# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os
import json
import copy
import logging

import qtawesome as qta
from functools import partial

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline.client import constants

from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    Context,
)
from ftrack_connect_pipeline_qt.utils import (
    BaseThread,
    str_version,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_browser import (
    ContextBrowser,
)

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.ui.assembler.base import (
    AssemblerBaseWidget,
    AssemblerListBaseWidget,
    ComponentBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search


class AssemblerDependenciesWidget(AssemblerBaseWidget):

    dependencies_resolved = QtCore.Signal(object)

    def __init__(self, assembler_client, parent=None):
        super(AssemblerDependenciesWidget, self).__init__(
            assembler_client, parent=parent
        )

    def build_header(self):
        # With refresh button on the right hand side
        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(QtWidgets.QVBoxLayout())
        header_widget.layout().setContentsMargins(0, 0, 0, 0)

        header_widget.layout().addStretch()
        self._refresh_button = CircularButton('sync', '#87E1EB')
        header_widget.layout().addWidget(
            self._refresh_button, alignment=QtCore.Qt.AlignRight
        )

        self.layout().addWidget(header_widget)

    def post_build(self):
        self._refresh_button.clicked.connect(self.refresh)
        self.dependencies_resolved.connect(self.on_dependencies_resolved)

    def refresh(self):
        # Add spinner
        super(AssemblerDependenciesWidget, self).refresh()

        self.model.reset()

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
            target_args=[self._assembler_client.context_selector.context_id],
        )
        thread.start()

    def _resolve_dependencies(self, context_id):
        try:
            return self._assembler_client.asset_manager.resolve_dependencies(
                context_id, self.on_dependencies_resolved_async
            )
        except:
            import traceback

            print(traceback.format_exc())

    def on_dependencies_resolved_async(self, result):
        if (
            self._assembler_client.import_mode
            != self._assembler_client.IMPORT_MODE_DEPENDENCIES
        ):
            return
        self.dependencies_resolved.emit(result)

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
            self._assembler_client.progress_widget.set_status(
                constants.WARNING_STATUS, user_message
            )

        self.scroll.widget().deleteLater()

        if len(versions or []) == 0:
            if user_message is None:
                self._assembler_client.progress_widget.set_status(
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
            self._assembler_client.progress_widget.set_status(
                constants.WARNING_STATUS, 'No loadable dependencies found!'
            )
            return

        # Create component list
        self._component_list = DependenciesListWidget(self)
        # self._asset_list.setStyleSheet('background-color: blue;')

        self.scroll.setWidget(self._component_list)

        # Will trigger list to be rebuilt.
        self.model.insertRows(0, components)


class AssemblerBrowserWidget(AssemblerBaseWidget):
    def __init__(self, assembler_client, parent=None):
        super(AssemblerBrowserWidget, self).__init__(
            assembler_client, parent=parent
        )

    def build_header(self):
        # Header with refresh button on the right hand side
        header_widget = QtWidgets.QWidget()
        header_widget.setLayout(QtWidgets.QVBoxLayout())
        header_widget.layout().setContentsMargins(2, 2, 2, 2)
        header_widget.layout().setSpacing(2)

        label = QtWidgets.QLabel('Filter on context:')
        label.setObjectName('gray')
        self.layout().addWidget(label)

        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QHBoxLayout())
        widget.layout().setContentsMargins(2, 2, 2, 2)
        widget.layout().setSpacing(4)

        self._context_browser = ContextBrowser(
            self._assembler_client.context_selector.entity,
            self._assembler_client.session,
        )
        widget.layout().addWidget(self._context_browser)

        self._search = Search()
        self._search.input_updated.connect(self._on_search)
        widget.layout().addWidget(self._search)

        self._refresh_button = CircularButton('sync', '#87E1EB')
        widget.layout().addWidget(self._refresh_button)

        header_widget.layout().addWidget(widget)

        self.layout().addWidget(header_widget)

        # Add toolbar

        toolbar_widget = QtWidgets.QWidget()
        toolbar_widget.setLayout(QtWidgets.QHBoxLayout())
        toolbar_widget.layout().setContentsMargins(0, 0, 0, 0)

        self._cb_show_non_compatible = QtWidgets.QCheckBox(
            'Show non-compatible assets'
        )
        toolbar_widget.layout().addWidget(self._cb_show_non_compatible)

        toolbar_widget.layout().addWidget(QtWidgets.QLabel(), 100)

        self._label_info = QtWidgets.QLabel('Listing XxX assets')
        self._label_info.setObjectName('gray')
        toolbar_widget.layout().addWidget(self._label_info)

        self._busy_widget = BusyIndicator()
        toolbar_widget.layout().addWidget(self._busy_widget)
        self._busy_widget.setVisible(True)

        self.layout().addWidget(toolbar_widget)

    def post_build(self):
        self._refresh_button.clicked.connect(self.refresh)

    def refresh(self):
        super(AssemblerBrowserWidget, self).refresh()

    def _on_search(self):
        pass


class DependenciesListWidget(AssemblerListBaseWidget):
    '''Custom asset manager list view'''

    def __init__(self, assembler_widget, parent=None):
        self._asset_widget_class = DependencyComponentWidget
        super(DependenciesListWidget, self).__init__(
            assembler_widget, parent=parent
        )

    def rebuild(self):
        '''Add all assets(components) again from model.'''

        # TODO: Save selection state

        # Group by context
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
                index, self._assembler_widget, self.model.event_manager
            )
            component_widget.set_component_and_definitions(
                component, definitions
            )
            self.layout().addWidget(component_widget)
            component_widget.clicked.connect(
                partial(self.asset_clicked, component_widget)
            )

        self.layout().addWidget(QtWidgets.QLabel(), 1000)


class BrowserListWidget(AssemblerListBaseWidget):
    '''Custom asset manager list view'''

    def __init__(self, assembler_widget, parent=None):
        self._asset_widget_class = BrowsedComponentWidget
        super(BrowserListWidget, self).__init__(
            assembler_widget, parent=parent
        )


class DependencyComponentWidget(ComponentBaseWidget):
    '''Widget representation of a minimal asset representation'''

    def __init__(
        self, index, assembler_widget, event_manager, title=None, parent=None
    ):
        super(DependencyComponentWidget, self).__init__(
            index, assembler_widget, event_manager, title=title, parent=parent
        )
        self.setMinimumHeight(25)

    def get_thumbnail_height(self):
        return 18

    def get_ident_widget(self):
        '''Asset name and component name.file_type'''
        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QHBoxLayout())
        widget.layout().setContentsMargins(0, 0, 0, 0)
        widget.layout().setSpacing(0)

        self._asset_name_widget = QtWidgets.QLabel()
        self._asset_name_widget.setObjectName('h4')

        widget.layout().addWidget(self._asset_name_widget)

        self._component_filename_widget = QtWidgets.QLabel()
        self._component_filename_widget.setObjectName('gray')

        widget.layout().addWidget(self._component_filename_widget)

        widget.layout().addWidget(QtWidgets.QLabel(), 100)

        return widget

    def get_version_widget(self):
        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QHBoxLayout())
        widget.layout().setContentsMargins(0, 0, 0, 0)
        widget.layout().setSpacing(0)

        # dash = QtWidgets.QLabel('-')
        # dash.setObjectName('h4')
        # widget.layout().addWidget(dash)

        self._version_nr_widget = QtWidgets.QLabel()
        widget.layout().addWidget(self._version_nr_widget)

        return widget

    def set_version(self, version_nr):
        if self._collapsed:
            self._version_nr_widget.setText('v{}  '.format(str(version_nr)))

    def set_latest_version(self, is_latest_version):
        color = '#935BA2' if is_latest_version else '#FFBA5C'
        self._version_nr_widget.setStyleSheet(
            'color: {}; font-weight: bold;'.format(color)
        )

    def set_component_and_definitions(self, component, definitions):
        '''Update widget from data'''
        super(DependencyComponentWidget, self).set_component_and_definitions(
            component, definitions
        )

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


class BrowsedComponentWidget(ComponentBaseWidget):
    '''Widget representation of a minimal asset representation'''

    def __init__(
        self, index, assembler_widget, event_manager, title=None, parent=None
    ):
        super(BrowsedComponentWidget, self).__init__(
            index, assembler_widget, event_manager, title=title, parent=parent
        )
        self.setMinimumHeight(40)

    def get_thumbnail_height(self):
        return 38


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
