# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os
import json
import copy
import time

from functools import partial

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline.client import constants
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    Context,
)
from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline_qt.utils import (
    BaseThread,
    center_widget,
    set_property,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)

from ftrack_connect_pipeline_qt.ui.assembler.base import (
    AssemblerBaseWidget,
    AssemblerListBaseWidget,
    ComponentBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import (
    VersionComboBox,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog


class AssemblerDependenciesWidget(AssemblerBaseWidget):

    dependencyResolveWarning = QtCore.Signal(object, object, object)
    dependenciesResolved = QtCore.Signal(object)

    @property
    def linked_only(self):
        return self._cb_linked_only.isChecked()

    def __init__(self, assembler_client, parent=None):
        super(AssemblerDependenciesWidget, self).__init__(
            assembler_client, parent=parent
        )

    def post_build(self):
        super(AssemblerDependenciesWidget, self).post_build()
        self._rebuild_button.clicked.connect(self.rebuild)
        self.dependenciesResolved.connect(self._on_dependencies_resolved)
        self.dependencyResolveWarning.connect(
            self._on_dependency_resolve_warning
        )
        self._cb_linked_only.clicked.connect(self.rebuild)

    def _get_header_widget(self):
        self._cb_linked_only = QtWidgets.QCheckBox('Linked dependencies only')
        self._cb_linked_only.setToolTip(
            'Only show linked assets, deselect and loadable assets on parent context(s) will be resolved'
        )
        self._cb_linked_only.setObjectName("gray")
        self._cb_linked_only.setChecked(True)
        return self._cb_linked_only

    def rebuild(self):
        if super(AssemblerDependenciesWidget, self).rebuild():

            self.scroll.setWidget(QtWidgets.QLabel(''))

            # Resolve version this context is depending on in separate thread
            thread = BaseThread(
                name='resolve_dependencies_thread',
                target=self._resolve_dependencies,
                target_args=[
                    self._assembler_client.context_selector.context_id,
                    {'linked_only': False}
                    if self.linked_only is False
                    else None,
                ],
            )
            thread.start()

    def _resolve_dependencies(self, context_id, options):
        try:
            return self._assembler_client.asset_manager.resolve_dependencies(
                context_id,
                self._on_dependencies_resolved_async,
                options=options,
            )
        except Exception as e:
            self.dependencyResolveWarning.emit(True, str(e), 'Error')
            raise

    def _on_dependencies_resolved_async(self, result):
        try:
            try:

                if (
                    self._assembler_client.assemble_mode
                    != self._assembler_client.ASSEMBLE_MODE_DEPENDENCIES
                ):
                    return

                resolved_versions = None
                user_message = None
                if isinstance(result, dict):
                    # Versions without a user message
                    resolved_versions = result['versions']
                else:
                    if isinstance(result, tuple):
                        # With user message?
                        if isinstance(result[0], dict):
                            resolved_version = result[0].get('versions') or []
                        if isinstance(result[1], dict):
                            user_data = result[1]
                            if 'message' in user_data:
                                user_message = user_data['message']
                if user_message:
                    self.dependencyResolveWarning.emit(
                        True, user_message, 'Error'
                    )

                if len(resolved_versions or []) == 0:
                    if user_message is None:
                        self.dependencyResolveWarning.emit(
                            False, 'No dependencies found!', 'No assets found'
                        )
                    return

                versions = [
                    resolved_version['entity']
                    for resolved_version in resolved_versions
                ]

                # Process versions, filter against
                self.logger.info(
                    'Resolved versions: {}'.format(
                        ','.join(
                            [str_version(v, with_id=True) for v in versions]
                        )
                    )
                )

                components = self.extract_components(versions)

                if (
                    self._assembler_client.assemble_mode
                    != self._assembler_client.ASSEMBLE_MODE_DEPENDENCIES
                ):
                    return

                if len(components) == 0:
                    self.dependencyResolveWarning.emit(
                        False,
                        'No loadable dependencies found!',
                        'No loadable dependencies found.',
                    )
                    return

                self.dependenciesResolved.emit(components)
            finally:
                self.stopBusyIndicator.emit()
        except RuntimeError as re:
            if str(re).find('Internal C++ object') == -1:
                raise
            # Ignore exception caused by a resolve that is not valid anymore

    def _on_dependency_resolve_warning(self, is_error, message, info_message):
        if is_error:
            self._assembler_client.progress_widget.set_status(
                constants.WARNING_STATUS, message
            )
        else:
            widget = QtWidgets.QWidget()
            widget.setLayout(QtWidgets.QVBoxLayout())
            label = QtWidgets.QLabel(message)
            label.setObjectName('gray-darker')
            widget.layout().addWidget(label)
            widget.layout().addWidget(QtWidgets.QLabel(), 100)
            self.scroll.setWidget(widget)
        self._label_info.setText(info_message)

    def _on_dependencies_resolved(self, components):

        # Create component list
        self._component_list = DependenciesListWidget(self)
        self.listWidgetCreated.emit(self._component_list)
        # self._asset_list.setStyleSheet('background-color: blue;')

        self.scroll.setWidget(self._component_list)

        # Will trigger list to be rebuilt.
        self.model.insertRows(0, components)

        self._label_info.setText(
            'Listing {} {}'.format(
                self.model.rowCount(),
                'dependencies' if self.model.rowCount() > 1 else 'dependency',
            )
        )


class AssemblerBrowserWidget(AssemblerBaseWidget):

    componentsFetched = QtCore.Signal(
        object, object
    )  # Emitted when a new chunk of versions has been loaded
    fetchMoreComponents = (
        QtCore.Signal()
    )  # Emitted when user requests to fetch more components
    allVersionsFetched = (
        QtCore.Signal()
    )  # Emitted when all versions has been fetched

    @property
    def context_path(self):
        '''Return a list with context path elements, cache it to improve performance.'''
        if (
            not self._cached_context_path_id
            or self._cached_context_path_id
            != self._entity_browser.entity['id']
        ):
            self._cached_context_path = [
                link['name'] for link in self._entity_browser.entity['link']
            ]
            self._cached_context_path_id = self._entity_browser.entity['id']
        return self._cached_context_path

    def __init__(self, assembler_client, parent=None):
        self._component_list = None
        super(AssemblerBrowserWidget, self).__init__(
            assembler_client, parent=parent
        )
        self._cached_context_path_id = None

    def pre_build(self):
        super(AssemblerBrowserWidget, self).pre_build()
        # Fetch entity, might not be loaded yet
        entity = self.get_context(False)

        self._entity_browser = EntityBrowser(
            self._assembler_client.parent(),
            self._assembler_client.session,
            mode=EntityBrowser.MODE_CONTEXT,
            entity=entity,
        )

    def _get_header_widget(self):
        self._entity_browser_navigator = (
            self._entity_browser.create_navigator()
        )
        return self._entity_browser_navigator

    def post_build(self):
        super(AssemblerBrowserWidget, self).post_build()
        self._rebuild_button.clicked.connect(self.rebuild)
        self._entity_browser.entityChanged.connect(self.rebuild)
        self.componentsFetched.connect(self._on_components_fetched)
        self.allVersionsFetched.connect(self._on_all_versions_fetched)
        self._search.inputUpdated.connect(self._on_search)

    def rebuild(self):
        '''Fetch assets beneath the current context, start on new query'''
        if super(AssemblerBrowserWidget, self).rebuild():

            if self._entity_browser.entity is None:
                # First time set
                self._entity_browser.set_entity(self.get_context())

            # Create viewport widget, component list with load more button
            widget = QtWidgets.QWidget()
            widget.setLayout(QtWidgets.QVBoxLayout())
            widget.layout().setContentsMargins(0, 0, 0, 0)
            widget.layout().setSpacing(1)

            self._component_list = BrowserListWidget(self)
            self._component_list.versionChanged.connect(
                self._on_version_changed
            )
            self.listWidgetCreated.emit(self._component_list)

            widget.layout().addWidget(self._component_list)

            self._fetch_more_button = QtWidgets.QPushButton('FETCH MORE...')
            self._fetch_more_button.setVisible(False)
            self._fetch_more_button.clicked.connect(self._fetch_more)
            widget.layout().addWidget(self._fetch_more_button)

            widget.layout().addWidget(QtWidgets.QLabel(), 100)

            self.scroll.setWidget(widget)

            context = self._entity_browser.entity

            # Find version beneath browsed entity, in chunks
            self._limit = self._assembler_client.asset_fetch_chunk_size
            self._tail = 0  # The current fetch position
            self.parent_ids = None
            self.fetched_version_ids = []
            self._recent_context_browsed = context

            thread = BaseThread(
                name='fetch_browsed_assets_thread',
                target=self._fetch_versions,
                target_args=[context],
            )
            thread.start()

    def reset(self):
        '''Reset browser entity ID back to current working context'''
        self._entity_browser.entity_id = self._assembler_client.context_id

    def _fetch_more(self):
        '''Continue previous query'''
        self._fetch_more_button.setVisible(False)
        if super(AssemblerBrowserWidget, self).rebuild(reset=False):
            self._tail += self._limit
            context = self._entity_browser.entity
            thread = BaseThread(
                name='fetch_more_browsed_assets_thread',
                target=self._fetch_versions,
                target_args=[context],
            )
            thread.start()

    def _recursive_get_descendant_ids(self, context):
        result = []
        if context.entity_type != 'Task':
            result.append(context['id'])
        if 'children' in context:
            self.session.populate(
                context, 'children'
            )  # Make sure we fetch fresh data
            for child in context['children']:
                if child.entity_type != "Task":
                    for context_id in self._recursive_get_descendant_ids(
                        child
                    ):
                        if not context_id in result:
                            result.append(context_id)
        return result

    def _fetch_versions(self, context):
        '''Search ftrack for versions beneath the given *context_id*'''
        try:
            if self.parent_ids is None:
                # First run, build list of children ID's (non tasks)
                self.parent_ids = self._recursive_get_descendant_ids(context)

            self.logger.info(
                'Fetching versions beneath context: {0} [{1}-{2}]'.format(
                    context, self._tail, self._tail + self._limit - 1
                )
            )
            task_sub_query = ''
            if context.entity_type == 'Task':
                task_sub_query = 'task.id is "{0}"'.format(context['id'])
            if len(self.parent_ids) > 0:
                if len(task_sub_query) > 0:
                    task_sub_query = '{} or '.format(task_sub_query)
                task_sub_query = '{0}task.parent.id in ({1})'.format(
                    task_sub_query,
                    ','.join(
                        [
                            '"{}"'.format(context_id)
                            for context_id in self.parent_ids
                        ]
                    ),
                )
            versions = []
            for version in self.session.query(
                'select id,task,version from AssetVersion where '
                ' is_latest_version=true and ({0}) offset {1} limit {2}'.format(
                    task_sub_query,
                    self._tail,
                    self._limit,
                )
            ):
                if not version['id'] in self.fetched_version_ids:
                    self.logger.debug(
                        'Got version: {}_v{}({})'.format(
                            version['asset']['name'],
                            version['version'],
                            version['id'],
                        )
                    )
                    versions.append(version)
                    self.fetched_version_ids.append(version['id'])

            if (
                self._recent_context_browsed != context
                or self._assembler_client.assemble_mode
                != self._assembler_client.ASSEMBLE_MODE_BROWSE
            ):
                # User is fast, have already traveled to a new context or switched mode
                return

            if len(versions) > 0:

                components = self.extract_components(versions)

                if (
                    self._recent_context_browsed != context
                    or self._assembler_client.assemble_mode
                    != self._assembler_client.ASSEMBLE_MODE_BROWSE
                ):
                    # User is fast, have already traveled to a new context
                    return

                self.componentsFetched.emit(components, len(versions))
            else:
                # We are done
                self.allVersionsFetched.emit()

        except RuntimeError as re:
            if str(re).find('Internal C++ object') == -1:
                raise
            # Ignore exception caused by a browse operation that is not valid anymore

    def _on_components_fetched(self, components, version_count):
        '''A chunk of versions has been obtained, filter > give setup and add to list'''
        # Will trigger list to be rebuilt.
        self.stopBusyIndicator.emit()
        self.model.insertRows(self.model.rowCount(), components)
        self._fetch_more_button.setVisible(version_count == self._limit)
        self.update()

    def _on_all_versions_fetched(self):
        self.stopBusyIndicator.emit()
        self.update()
        if self.model.rowCount() == 0:
            l = QtWidgets.QLabel(
                '<html><i>No assets found, please refine your search!</i></html>'
            )
            l.setObjectName("gray-darker")
            self.scroll.setWidget(center_widget(l))
            self._label_info.setText('No assets found')

    def update(self):
        '''Update UI on new fetched components'''
        super(AssemblerBrowserWidget, self).update()
        if self.model.rowCount() > 0:
            self._label_info.setText(
                'Listing {} asset{}'.format(
                    self.model.rowCount(),
                    's' if self.model.rowCount() > 1 else '',
                )
            )
        else:
            self._label_info.setText('No assets found')

        self._assembler_client.run_button_no_load.setEnabled(
            self._loadable_count > 0
        )
        self._assembler_client.run_button.setEnabled(self._loadable_count > 0)

    def _on_search(self, text):
        if self._component_list:
            self._component_list.on_search(text)

    def _on_version_changed(self, widget, version_entity):
        '''User request a change of version, check that the new version
        has the component and it matches.'''
        current_component = self._assembler_client.session.query(
            'name, file_type from Component where id={}'.format(
                widget.component_id
            )
        ).one()
        component = self._assembler_client.session.query(
            'name, file_type from Component where version.id={} and name={}'.format(
                version_entity['id'], current_component['name']
            )
        ).first()
        # Has the same component name?
        error_message = None
        if component is None:
            error_message = (
                'There is no component by the name {} at version {}!'.format(
                    current_component['name'], version_entity['version']
                )
            )
        # Check file extension
        elif component['file_type'] != current_component['file_type']:
            error_message = (
                'The version {} component file type "{}" differs!'.format(
                    version_entity['version'], component['file_type']
                )
            )
        if not error_message:
            # Set the new component
            matching_definitions = self.model.data(widget.index)[1]
            # Replace version ID for importer
            for definition in matching_definitions:
                for context in definition['contexts']:
                    for stage in context['stages']:
                        if stage['name'] == 'context':
                            for plugin in stage['plugins']:
                                if 'options' in plugin:
                                    options = plugin['options']
                                    options['version_id'] = version_entity[
                                        'id'
                                    ]
                                    options['version_number'] = version_entity[
                                        'version'
                                    ]
            location = self.session.pick_location()
            self.model.setData(
                widget.index,
                (
                    component,
                    matching_definitions,
                    location.get_component_availability(component),
                ),
            )
        else:
            dialog.ModalDialog(
                self._assembler_client,
                title='Change Import Version',
                message=error_message,
            )
            widget.set_version(current_component['version'])  # Revert
            return


class DependenciesListWidget(AssemblerListBaseWidget):
    '''Custom asset manager list view'''

    def __init__(self, assembler_widget, parent=None):
        self._asset_widget_class = DependencyComponentWidget
        super(DependenciesListWidget, self).__init__(
            assembler_widget, parent=parent
        )

    def post_build(self):
        super(DependenciesListWidget, self).post_build()
        self._model.rowsInserted.connect(self._on_dependencies_added)
        self._model.modelReset.connect(self._on_dependencies_added)
        self._model.rowsRemoved.connect(self._on_dependencies_added)
        self._model.dataChanged.connect(self._on_dependencies_added)

    def _on_dependencies_added(self, *args):
        self.rebuild()
        selection = self.selection()
        if selection:
            self.selectionUpdated.emit(selection)

    def rebuild(self):
        '''Add all assets(components) again from model.'''

        # TODO: Save selection state

        # Group by context
        prev_context_id = None
        for row in range(self.model.rowCount()):
            index = self.model.createIndex(row, 0, self.model)

            (component, definitions, availability) = self.model.data(index)

            context_id = component['version']['task']['id']

            # Add a grouping element?

            if prev_context_id is None or context_id != prev_context_id:

                context_entity = self.model.session.query(
                    'select link, name, parent, parent.name from Context where id '
                    'is "{}"'.format(context_id)
                ).one()

                widget = AssemblerDependencyContextLabel()
                widget.setLayout(QtWidgets.QHBoxLayout())
                widget.layout().setContentsMargins(8, 10, 8, 0)
                widget.layout().setSpacing(2)

                # Append thumbnail
                thumbnail_widget = Context(self.model.session)
                # self.thumbnail_widget.setScaledContents(True)

                thumbnail_widget.setMinimumWidth(40)
                thumbnail_widget.setMinimumHeight(40)
                thumbnail_widget.setMaximumWidth(40)
                thumbnail_widget.setMaximumHeight(40)
                thumbnail_widget.load(context_entity['id'])
                widget.layout().addWidget(thumbnail_widget)

                # Append a context label
                entity_info = AssemblerEntityInfo()
                entity_info.setMinimumHeight(40)
                entity_info.setMaximumHeight(40)
                entity_info.set_entity(context_entity)

                widget.layout().addWidget(entity_info)

                self.layout().addWidget(widget)

            # Append component accordion

            component_widget = self._asset_widget_class(
                index, self._assembler_widget, self.model.event_manager
            )
            set_property(
                component_widget,
                'first',
                'true' if row == 0 else 'false',
            )
            if availability < 100.0:
                component_widget.set_warning_message(
                    'Not available in your current location - please transfer over!'
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

    versionChanged = QtCore.Signal(object, object)

    def __init__(self, assembler_widget, parent=None):
        self._asset_widget_class = BrowsedComponentWidget
        self.prev_search_text = None
        super(BrowserListWidget, self).__init__(
            assembler_widget, parent=parent
        )

    def build(self):
        super(BrowserListWidget, self).build()
        self.layout().addWidget(QtWidgets.QLabel(), 100)

    def post_build(self):
        super(BrowserListWidget, self).post_build()
        self.model.rowsInserted.connect(self._on_components_added)
        self.model.dataChanged.connect(self._on_component_set)

    def _on_component_set(self, index_first, unused_index_last):
        current_widget = self.get_widget(index_first)
        updated_widget = self._build_widget(index_first)
        updated_widget.selected = current_widget.selected
        self.layout().replaceWidget(current_widget, updated_widget)

        self.refresh()
        selection = self.selection()
        if selection is not None:
            self.selectionUpdated.emit(selection)

    def _on_components_added(self, index, first, last):
        '''Add components recently added from model to list.'''
        for row in range(first, last + 1):
            index = self.model.createIndex(row, 0, self.model)
            self.layout().insertWidget(
                self.layout().count() - 1, self._build_widget(index)
            )
        self.refresh()
        selection = self.selection()
        if selection is not None:
            self.selectionUpdated.emit(selection)

    def _build_widget(self, index):
        '''Build component accordion widget'''
        (component, definitions, availability) = self.model.data(index)
        component_widget = self._asset_widget_class(
            index, self._assembler_widget, self.model.event_manager
        )
        set_property(
            component_widget,
            'first',
            'true' if index.row() == 0 else 'false',
        )
        if availability < 100.0:
            component_widget.set_warning_message(
                'Not available in your current location - please transfer over!'
            )
        component_widget.set_component_and_definitions(component, definitions)

        component_widget.clicked.connect(
            partial(self.asset_clicked, component_widget)
        )
        component_widget.versionChanged.connect(
            partial(self._on_version_change, component_widget)
        )
        return component_widget

    def refresh(self, search_text=None):
        if search_text is None:
            search_text = self.prev_search_text
        '''Update visibility based on search'''
        for component_widget in self.assets:
            component_widget.setVisible(
                len(search_text or '') == 0
                or component_widget.matches(search_text)
            )

    def on_search(self, text):
        if text != self.prev_search_text:
            self.refresh(text.lower())
            self.prev_search_text = text

    def _on_version_change(self, widget, version_entity):
        self.versionChanged.emit(widget, version_entity)


class DependencyComponentWidget(ComponentBaseWidget):
    '''Widget representation of a minimal asset representation'''

    def __init__(
        self, index, assembler_widget, event_manager, title=None, parent=None
    ):
        super(DependencyComponentWidget, self).__init__(
            index, assembler_widget, event_manager, title=title, parent=parent
        )

    def get_height(self):
        return 32

    def get_thumbnail_height(self):
        return 32

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

        # widget.layout().addWidget(QtWidgets.QLabel(), 100)

        return widget

    def get_version_widget(self):
        self._version_nr_widget = QtWidgets.QLabel('?')
        return self._version_nr_widget

    def set_version(self, version_entity):
        self._version_nr_widget.setText(
            'v{}  '.format(str(version_entity['version']))
        )

    def set_latest_version(self, is_latest_version):
        color = '#A5A8AA' if is_latest_version else '#FFBA5C'
        self._version_nr_widget.setStyleSheet(
            'color: {}; font-weight: bold;'.format(color)
        )


class BrowsedComponentWidget(ComponentBaseWidget):
    '''Widget representation of a minimal asset representation'''

    versionChanged = QtCore.Signal(object)

    def __init__(
        self, index, assembler_widget, event_manager, title=None, parent=None
    ):
        super(BrowsedComponentWidget, self).__init__(
            index, assembler_widget, event_manager, title=title, parent=parent
        )

    def get_height(self):
        return 32

    def get_thumbnail_height(self):
        return 32

    def get_ident_widget(self):
        '''Asset name and component name.file_type'''
        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())
        widget.layout().setContentsMargins(5, 0, 0, 0)
        widget.layout().setSpacing(2)

        # Add context path, relative to browser context
        self._path_widget = QtWidgets.QLabel()
        self._path_widget.setObjectName("gray-dark")

        widget.layout().addWidget(self._path_widget)

        lower_widget = QtWidgets.QWidget()
        lower_widget.setLayout(QtWidgets.QHBoxLayout())
        lower_widget.layout().setContentsMargins(0, 0, 0, 0)
        lower_widget.layout().setSpacing(0)

        self._asset_name_widget = QtWidgets.QLabel()
        self._asset_name_widget.setObjectName('h4')

        lower_widget.layout().addWidget(self._asset_name_widget)

        self._component_filename_widget = QtWidgets.QLabel()
        self._component_filename_widget.setObjectName('gray')

        lower_widget.layout().addWidget(self._component_filename_widget)

        widget.layout().addWidget(lower_widget)

        return widget

    def get_version_widget(self):
        self._version_nr_widget = AssemblerVersionComboBox(self.session)
        self._version_nr_widget.versionChanged.connect(
            self._on_version_changed
        )
        return self._version_nr_widget

    def set_context_id(self, context_id):
        super(BrowsedComponentWidget, self).set_context_id(context_id)
        self._version_nr_widget.set_context_id(self._context_id)

    def set_version(self, version_entity):
        self._version_nr_widget.set_version_entity(version_entity)

    def set_latest_version(self, is_latest_version):
        color = '#A5A8AA' if is_latest_version else '#FFBA5C'
        self._version_nr_widget.setStyleSheet(
            'color: {}; font-weight: bold;'.format(color)
        )

    def set_component_and_definitions(self, component, definitions):
        super(BrowsedComponentWidget, self).set_component_and_definitions(
            component, definitions
        )
        # Calculate path
        parent_path = [
            link['name'] for link in component['version']['task']['link']
        ]
        context_path = self._assembler_widget.context_path
        index = 0
        while parent_path[index].lower() == context_path[index].lower():
            index += 1
            if index == len(context_path):
                break
        sub_path = parent_path[index:]
        self._path_widget.setText(' / '.join(sub_path))
        self._path_widget.setVisible(len(sub_path) > 0)

    def _on_version_changed(self, entity_version):
        '''Another version has been selected, emit event.'''
        self.versionChanged.emit(entity_version)

    def matches(self, search_text):
        '''Do a simple match if this search text matches my attributes'''
        if self._context_id.lower().find(search_text) > -1:
            return True
        if self._context_name.lower().find(search_text) > -1:
            return True
        if self._asset_name_widget.text().lower().find(search_text) > -1:
            return True
        if self._component_name.lower().find(search_text) > -1:
            return True
        if self._path_widget.text().lower().find(search_text) > -1:
            return True
        return False


class AssemblerEntityInfo(QtWidgets.QWidget):
    '''Entity path widget.'''

    pathReady = QtCore.Signal(object)

    def __init__(self, parent=None):
        '''Instantiate the entity path widget.'''
        super(AssemblerEntityInfo, self).__init__(parent=parent)

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
        # self._path_field.setObjectName('gray')
        self.layout().addWidget(self._path_field)

        self.layout().addStretch()

    def post_build(self):
        self.pathReady.connect(self.on_path_ready)

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
        self.pathReady.emit(parents)

    def on_path_ready(self, parents):
        '''Set current path to *names*.'''
        self._path_field.setText(os.sep.join([p['name'] for p in parents[:]]))


class AssemblerVersionComboBox(VersionComboBox):
    def __init__(self, session, parent=None):
        super(AssemblerVersionComboBox, self).__init__(session, parent=parent)

    def _add_version(self, version):
        self.addItem(str("v{}".format(version['version'])), version['id'])


class AssemblerDependencyContextLabel(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super(AssemblerDependencyContextLabel, self).__init__(parent=parent)
