# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

from functools import partial

from Qt import QtCore, QtWidgets

import ftrack_connect_pipeline.constants as core_constants
from ftrack_connect_pipeline.client import constants
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    Context,
)
from ftrack_connect_pipeline.utils import str_version
from ftrack_connect_pipeline_qt.utils import (
    BaseThread,
    center_widget,
    set_property,
    clear_layout,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)

from ftrack_connect_pipeline_qt.ui.assembler.base import (
    AssemblerBaseWidget,
    AssemblerListBaseWidget,
    ComponentBaseWidget,
    AssemblerEntityInfo,
    AssemblerVersionComboBox,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog


class AssemblerDependenciesWidget(AssemblerBaseWidget):
    '''Dependencies widget'''

    dependencyResolveWarning = QtCore.Signal(
        object, object, object
    )  # Emitted when an error/warning message needs to be displayed
    dependenciesResolved = QtCore.Signal(
        object
    )  # Emitted from background thread when components has been extracted

    @property
    def linked_only(self):
        '''Return True if user has chosen to return linked dependencies only'''
        return self._cb_linked_only.isChecked()

    def __init__(self, client):
        '''
        Instantiate the dependencies widget

        :param client: :class:`~ftrack_connect_pipeline_qt.client.load.QtAssemblerWidget` instance
        '''
        super(AssemblerDependenciesWidget, self).__init__(client)

    def post_build(self):
        '''(Override)'''
        super(AssemblerDependenciesWidget, self).post_build()
        self._rebuild_button.clicked.connect(self.rebuild)
        self.dependenciesResolved.connect(self._on_dependencies_resolved)
        self.dependencyResolveWarning.connect(
            self._on_dependency_resolve_warning
        )
        self._cb_linked_only.clicked.connect(self.rebuild)

    def _get_header_widget(self):
        '''(Override) Build dependency option widgets and add to header'''
        self._cb_linked_only = QtWidgets.QCheckBox('Linked dependencies only')
        self._cb_linked_only.setToolTip(
            'Only show linked assets, deselect and loadable assets on parent context(s) will be resolved'
        )
        self._cb_linked_only.setObjectName("gray")
        self._cb_linked_only.setChecked(True)
        return self._cb_linked_only

    def rebuild(self, reset=True):
        '''(Override) Resolve dependencies in separate thread'''
        if super(AssemblerDependenciesWidget, self).rebuild():

            self.scroll.setWidget(QtWidgets.QLabel(''))

            # Resolve version this context is depending on in separate thread
            thread = BaseThread(
                name='resolve_dependencies_thread',
                target=self._resolve_dependencies,
                target_args=[
                    self.client.context_id,
                    {'linked_only': False}
                    if self.linked_only is False
                    else None,
                ],
            )
            thread.start()

    def _resolve_dependencies(self, context_id, options):
        '''(Background thread) Resolve dependencies from ftrack'''
        try:
            return self.client.asset_manager.resolve_dependencies(
                context_id,
                self._on_dependencies_resolved_async,
                options=options,
            )
        except Exception as e:
            self.dependencyResolveWarning.emit(True, str(e), 'Error')
            raise

    def _on_dependencies_resolved_async(self, result):
        '''(Background thread) Process the resolved dependencies based on what we can load'''
        try:
            try:

                if (
                    self.client.assemble_mode
                    != self.client.ASSEMBLE_MODE_DEPENDENCIES
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
                    self.client.assemble_mode
                    != self.client.ASSEMBLE_MODE_DEPENDENCIES
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
                self.loadError.emit('An internal error occurred')
                raise
            # Ignore exception caused by a resolve that is not valid anymore
        except:
            self.loadError.emit('An internal exception occurred')
            raise

    def _on_dependency_resolve_warning(self, is_error, message, info_message):
        '''Display error/warning message from resolve process'''
        if is_error:
            self.loadError.emit(message)
        else:
            widget = QtWidgets.QWidget()
            widget.setLayout(QtWidgets.QVBoxLayout())
            label = QtWidgets.QLabel(message)
            label.setObjectName('gray-darker')
            widget.layout().addWidget(label)
            widget.layout().addWidget(QtWidgets.QLabel(), 100)
            self.scroll.setWidget(widget)
        self._label_info.setText(info_message)
        self.client.run_button_no_load.setEnabled(self.loadable_count > 0)
        self.client.run_button.setEnabled(self.loadable_count > 0)

    def _on_dependencies_resolved(self, components):
        '''Create and deploy list of resolved components'''
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
    '''Widget driving manual user browse of assets (components)'''

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

    def __init__(self, client):
        '''
        Instantiate the browser widget

        :param client:  :class:`~ftrack_connect_pipeline_qt.client.load.QtAssemblerWidget` instance
        '''
        self._component_list = None
        super(AssemblerBrowserWidget, self).__init__(client)
        self._cached_context_path_id = None

    def pre_build(self):
        '''(Override)'''
        super(AssemblerBrowserWidget, self).pre_build()
        # Fetch entity, might not be loaded yet

        self._entity_browser = EntityBrowser(
            self.client,
            self.client.session,
            mode=EntityBrowser.MODE_CONTEXT,
            entity=self.client.context,
        )

    def _get_header_widget(self):
        '''Add the entity browser navigator and use it as header widget'''
        self._entity_browser_navigator = (
            self._entity_browser.create_navigator()
        )
        return self._entity_browser_navigator

    def post_build(self):
        '''(Override)'''
        super(AssemblerBrowserWidget, self).post_build()
        self._rebuild_button.clicked.connect(self.rebuild)
        self._entity_browser.entityChanged.connect(self.rebuild)
        self.componentsFetched.connect(self._on_components_fetched)
        self.allVersionsFetched.connect(self._on_all_versions_fetched)
        self._search.inputUpdated.connect(self._on_search)

    def rebuild(self, reset=True):
        '''(Override) Fetch assets beneath the current context, start on new query'''
        if super(AssemblerBrowserWidget, self).rebuild(reset=reset):

            if self._entity_browser.entity is None:
                # First time set
                self._entity_browser.entity = self.client.context

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
            self._limit = self.client.asset_fetch_chunk_size
            self._tail = 0  # The current fetch position
            self.fetched_version_ids = []
            self._recent_context_browsed = context

            thread = BaseThread(
                name='fetch_browsed_assets_thread',
                target=self._fetch_versions_async,
                target_args=[context],
            )
            thread.start()

    def reset(self):
        '''(Override) Reset browser entity ID back to current working context'''
        self._entity_browser.entity_id = self.client.context_id

    def _fetch_more(self):
        '''Continue previous query and fetch more assets'''
        self._fetch_more_button.setVisible(False)
        if super(AssemblerBrowserWidget, self).rebuild(reset=False):
            self._tail += self._limit
            context = self._entity_browser.entity
            thread = BaseThread(
                name='fetch_more_browsed_assets_thread',
                target=self._fetch_versions_async,
                target_args=[context],
            )
            thread.start()

    def _fetch_versions_async(self, context):
        '''(Background thread) Search ftrack for versions beneath the given *context_id*'''
        try:

            self.logger.info(
                'Fetching versions beneath context: {0} [{1}-{2}]'.format(
                    context, self._tail, self._tail + self._limit - 1
                )
            )
            versions = []
            for version in self.session.query(
                'select components.name,components.file_type,id,version,date,comment,is_latest_version,thumbnail_url,'
                'asset.id,asset.name,asset.type.id,task.link,task.name,status.id,status.name,user.id '
                'from AssetVersion where is_latest_version=true and ('
                'asset.context_id in ('
                'select id from TypedContext where ancestors.id is "{0}"'
                ') or '
                'asset.context_id is "{0}" or '
                'asset.project_id is "{0}" or '
                'task_id is "{0}"'
                ') offset {1} limit {2}'.format(
                    context['id'], self._tail, self._limit
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
                or self.client.assemble_mode
                != self.client.ASSEMBLE_MODE_BROWSE
            ):
                # User is fast, have already traveled to a new context or switched mode
                return

            if len(versions) > 0:

                components = self.extract_components(versions)

                if (
                    self._recent_context_browsed != context
                    or self.client.assemble_mode
                    != self.client.ASSEMBLE_MODE_BROWSE
                ):
                    # User is fast, have already traveled to a new context
                    return

                self.componentsFetched.emit(components, len(versions))
            else:
                # We are done
                self.allVersionsFetched.emit()

        except RuntimeError as re:
            if str(re).find('Internal C++ object') == -1:
                self.loadError.emit('An internal error occurred')
                raise
            # Ignore exception caused by a browse operation that is not valid anymore
        except:
            self.loadError.emit('An internal exception occurred')
            raise

    def _on_components_fetched(self, components, version_count):
        '''A chunk of versions has been obtained'''
        self.stopBusyIndicator.emit()
        # Add components to model, will trigger list to be rebuilt.
        self.model.insertRows(self.model.rowCount(), components)
        self._fetch_more_button.setVisible(version_count == self._limit)
        self.update()

    def _on_all_versions_fetched(self):
        '''No more versions to fetch'''
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

        self.client.run_button_no_load.setEnabled(self._loadable_count > 0)
        self.client.run_button.setEnabled(self._loadable_count > 0)

    def _on_search(self, text):
        '''Filter list on free text search'''
        if self._component_list:
            self._component_list.on_search(text)

    def _on_version_changed(self, widget, version_id):
        '''User request a change of version, check that the new version
        has the component and it matches.'''
        version_entity = self.client.session.query(
            'AssetVersion where id={}'.format(version_id)
        ).one()
        current_component = self.client.session.query(
            'Component where id={}'.format(widget.component_id)
        ).one()
        component = self.client.session.query(
            'Component where version.id={} and name={}'.format(
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
                for plugin in definition.get_all(
                    type=core_constants.CONTEXT,
                    category=core_constants.PLUGIN,
                ):
                    if 'options' in plugin:
                        options = plugin['options']
                        options['version_id'] = version_entity['id']
                        options['version_number'] = version_entity['version']
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
                self.client,
                title='Change Import Version',
                message=error_message,
            )
            widget.set_version(current_component['version'])  # Revert
            return


class DependenciesListWidget(AssemblerListBaseWidget):
    """List of assets evaluated as dependencies on the current context"""

    def __init__(self, assembler_widget, parent=None):
        '''
        Instantiate the dependency list widget

        :param assembler_widget: :class:`~ftrack_connect_pipeline_qt.ui.assembler.base.AssemblerBaseWidget` instance
        :param parent: The parent dialog or frame
        '''
        self._asset_widget_class = DependencyComponentWidget
        super(DependenciesListWidget, self).__init__(
            assembler_widget, parent=parent
        )

    def post_build(self):
        '''(Override)'''
        super(DependenciesListWidget, self).post_build()
        self._model.rowsInserted.connect(self._on_dependencies_added)
        self._model.modelReset.connect(self._on_dependencies_added)
        self._model.rowsRemoved.connect(self._on_dependencies_added)
        self._model.dataChanged.connect(self._on_dependencies_added)

    def _on_dependencies_added(self, *args):
        '''Model has been updated'''
        self.rebuild()
        selection = self.selection()
        if selection:
            self.selectionUpdated.emit(selection)

    def rebuild(self):
        '''Add all assets(components) again from model.'''
        # TODO: Save selection state
        clear_layout(self.layout())
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

                widget = QtWidgets.QFrame()
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
                entity_info.entity = context_entity

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
                component_widget.warning_message = 'Not available in your current location - please transfer over!'
            component_widget.set_component_and_definitions(
                component, definitions
            )
            self.layout().addWidget(component_widget)
            component_widget.clicked.connect(
                partial(self.asset_clicked, component_widget)
            )

        self.layout().addWidget(QtWidgets.QLabel(), 1000)
        self.refreshed.emit()


class BrowserListWidget(AssemblerListBaseWidget):
    """List of assets beneath the browsed context"""

    versionChanged = QtCore.Signal(object, object)

    def __init__(self, assembler_widget, parent=None):
        '''
        Instantiate the dependency list widget

        :param assembler_widget: :class:`~ftrack_connect_pipeline_qt.ui.assembler.base.AssemblerBaseWidget` instance
        :param parent: The parent dialog or frame
        '''
        self._asset_widget_class = BrowserComponentWidget
        self.prev_search_text = None
        super(BrowserListWidget, self).__init__(
            assembler_widget, parent=parent
        )

    def build(self):
        '''(Override)'''
        super(BrowserListWidget, self).build()
        self.layout().addWidget(QtWidgets.QLabel(), 100)

    def post_build(self):
        '''(Override)'''
        super(BrowserListWidget, self).post_build()
        self.model.rowsInserted.connect(self._on_components_added)
        self.model.dataChanged.connect(
            self._on_component_set
        )  # Support change version > change component

    def rebuild(self):
        pass

    def _on_component_set(self, index_first, unused_index_last):
        '''Replace an asset with another (version)'''
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
            component_widget.warning_message = 'Not available in your current location - please transfer over!'

        component_widget.set_component_and_definitions(component, definitions)

        component_widget.clicked.connect(
            partial(self.asset_clicked, component_widget)
        )
        component_widget.versionChanged.connect(
            partial(self._on_version_change, component_widget)
        )
        return component_widget

    def refresh(self, search_text=None):
        '''Update visibility based on search'''
        if search_text is None:
            search_text = self.prev_search_text
        for component_widget in self.assets:
            component_widget.setVisible(
                len(search_text or '') == 0
                or component_widget.matches(search_text)
            )

    def on_search(self, text):
        '''Search input text change callback'''
        if text != self.prev_search_text:
            self.refresh(text.lower())
            self.prev_search_text = text

    def _on_version_change(self, widget, version_id):
        '''Another version has been selected by user, relay event passing on *version_id*'''
        self.versionChanged.emit(widget, version_id)


class DependencyComponentWidget(ComponentBaseWidget):
    '''Widget representation of a dependency asset (component)'''

    def __init__(self, index, assembler_widget, event_manager, parent=None):
        '''
        Initialize dependency asset widget

        :param index: index of this asset has in list
        :param assembler_widget: :class:`~ftrack_connect_pipeline_qt.ui.assembler.base.AssemblerBaseWidget` instance
        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param parent: the parent dialog or frame
        '''
        super(DependencyComponentWidget, self).__init__(
            index, assembler_widget, event_manager, parent=parent
        )

    def get_height(self):
        '''(Override)'''
        return 32

    def get_thumbnail_height(self):
        '''(Override)'''
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
        '''(Override)'''
        self._version_nr_widget = QtWidgets.QLabel('?')
        return self._version_nr_widget

    def set_version(self, version_entity):
        '''(Override)'''
        self._version_nr_widget.setText(
            'v{}  '.format(str(version_entity['version']))
        )

    def set_latest_version(self, is_latest_version):
        '''(Override)'''
        color = '#A5A8AA' if is_latest_version else '#FFBA5C'
        self._version_nr_widget.setStyleSheet(
            'color: {}; font-weight: bold;'.format(color)
        )


class BrowserComponentWidget(ComponentBaseWidget):
    '''Widget representation of a browsed asset (component)'''

    versionChanged = QtCore.Signal(object)  # Emitted when user changes version

    def __init__(self, index, assembler_widget, event_manager, parent=None):
        '''
        Initialize browsed asset widget

        :param index: index of this asset has in list
        :param assembler_widget: :class:`~ftrack_connect_pipeline_qt.ui.assembler.base.AssemblerBaseWidget` instance
        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param parent: the parent dialog or frame
        '''
        super(BrowserComponentWidget, self).__init__(
            index, assembler_widget, event_manager, parent=parent
        )

    @property
    def context_id(self):
        '''Return the context id of this asset'''
        return self._context_id

    @context_id.setter
    def context_id(self, value):
        '''Set the context id of this asset'''
        self._context_id = value
        self._version_nr_widget.set_context_id(value)

    def get_height(self):
        '''(Override)'''
        return 32

    def get_thumbnail_height(self):
        '''(Override)'''
        return 32

    def get_ident_widget(self):
        '''Build and return the main widget identifying the component'''
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
        '''(Override)'''
        self._version_nr_widget = AssemblerVersionComboBox(self.session)
        self._version_nr_widget.versionChanged.connect(
            self._on_version_changed
        )
        return self._version_nr_widget

    def set_version(self, version_entity):
        '''(Override)'''
        self._version_nr_widget.set_version_entity(version_entity)

    def set_latest_version(self, is_latest_version):
        '''(Override)'''
        color = '#A5A8AA' if is_latest_version else '#FFBA5C'
        self._version_nr_widget.setStyleSheet(
            'color: {}; font-weight: bold;'.format(color)
        )

    def set_component_and_definitions(self, component, definitions):
        '''(Override)'''
        super(BrowserComponentWidget, self).set_component_and_definitions(
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

    def _on_version_changed(self, version_id):
        '''Another version has been selected by user, relay event passing on *version_id*'''
        self.versionChanged.emit(version_id)

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
