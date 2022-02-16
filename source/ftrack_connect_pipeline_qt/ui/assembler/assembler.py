# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import os
import json
import copy
import time

import qtawesome as qta
from functools import partial

from Qt import QtCore, QtWidgets
import shiboken2

from ftrack_connect_pipeline.client import constants

from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import (
    Context,
)
from ftrack_connect_pipeline_qt.utils import (
    BaseThread,
    str_version,
    center_widget,
    set_property,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)

from ftrack_connect_pipeline_qt.ui.assembler.base import (
    AssemblerBaseWidget,
    AssemblerListBaseWidget,
    ComponentBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.ui.utility.widget.version_selector import (
    VersionComboBox,
)


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
        self._rebuild_button = CircularButton('sync', '#87E1EB')
        header_widget.layout().addWidget(
            self._rebuild_button, alignment=QtCore.Qt.AlignRight
        )

        self.layout().addWidget(header_widget)

    def post_build(self):
        self._rebuild_button.clicked.connect(self.rebuild)
        self.dependencies_resolved.connect(self.on_dependencies_resolved)

    def rebuild(self):
        print('@@@ AssemblerDependenciesWidget::rebuild()')
        # Create spinner
        self._busy_widget = BusyIndicator()
        self.scroll.setWidget(center_widget(self._busy_widget, 30, 30))
        self._busy_widget.start()

        super(AssemblerDependenciesWidget, self).rebuild()

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

        components = self.extract_components(
            [resolved_version['entity'] for resolved_version in versions]
        )

        if len(components) == 0:
            self._assembler_client.progress_widget.set_status(
                constants.WARNING_STATUS, 'No loadable dependencies found!'
            )
            return

        # Create component list
        self._component_list = DependenciesListWidget(self)
        # self._asset_list.setStyleSheet('background-color: blue;')

        self._busy_widget.stop()
        self._busy_widget = None

        self.scroll.setWidget(self._component_list)

        # Will trigger list to be rebuilt.
        self.model.insertRows(0, components)


class AssemblerBrowserWidget(AssemblerBaseWidget):

    componentsFetched = QtCore.Signal(
        object
    )  # Emitted when a new chunk of versions has been loaded
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
        # if not entity:
        #     # Need one entity, choose first active project
        #     entity = self.session.query(
        #         'select link, name, parent, parent.name from Project where status is active'
        #     ).first()
        #     if entity is None:
        #         # Any project
        #         entity = self.session.query(
        #             'select link, name from Project'
        #         ).first()
        #         if entity is None:
        #             self.layout().addWidget(
        #                 'No entity given, and no project found!'
        #             )
        #             raise Exception('No entity given, and no project found!')
        self._entity_browser = EntityBrowser(
            session=self._assembler_client.session,
            mode=EntityBrowser.MODE_CONTEXT,
            entity=entity,
            parent=self._assembler_client,
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

        self._entity_browser_navigator = (
            self._entity_browser.create_navigator()
        )
        widget.layout().addWidget(self._entity_browser_navigator)

        self._rebuild_button = CircularButton('sync', '#87E1EB')
        widget.layout().addWidget(self._rebuild_button)

        header_widget.layout().addWidget(widget)

        self.layout().addWidget(header_widget)

        # Add toolbar

        toolbar_widget = QtWidgets.QWidget()
        toolbar_widget.setLayout(QtWidgets.QHBoxLayout())
        toolbar_widget.layout().setContentsMargins(0, 0, 0, 0)

        self._cb_show_non_compatible = QtWidgets.QCheckBox(
            'Show non-compatible assets'
        )
        self._cb_show_non_compatible.setObjectName("gray")
        toolbar_widget.layout().addWidget(self._cb_show_non_compatible)

        toolbar_widget.layout().addWidget(QtWidgets.QLabel(), 100)

        self._search = Search()
        toolbar_widget.layout().addWidget(self._search)

        self._label_info = QtWidgets.QLabel('Listing assets')
        self._label_info.setObjectName('gray')
        toolbar_widget.layout().addWidget(self._label_info)

        self._busy_widget = BusyIndicator(start=False)
        toolbar_widget.layout().addWidget(self._busy_widget)
        self._busy_widget.setMinimumSize(QtCore.QSize(16, 16))
        self._busy_widget.setVisible(False)

        self.layout().addWidget(toolbar_widget)

    def post_build(self):
        self._rebuild_button.clicked.connect(self.rebuild)
        self._cb_show_non_compatible.clicked.connect(self.rebuild)
        self._entity_browser.entityChanged.connect(self.rebuild)
        self.componentsFetched.connect(self._on_components_fetched)
        self.allVersionsFetched.connect(self._on_all_versions_fetched)
        self._search.input_updated.connect(self._on_search)

    def rebuild(self):
        print('@@@ AssemblerBrowserWidget::rebuild()')
        super(AssemblerBrowserWidget, self).rebuild()

        if self._entity_browser.entity is None:
            # First time set
            self._entity_browser.set_entity(self.get_context())

        # Create component list
        self._component_list = BrowserListWidget(self)

        self.scroll.setWidget(self._component_list)

        self._label_info.setText('Listing assets')

        # Find version beneath browsed entity, in chunks
        self._limit = 5  # Amount of assets to fetch at a time

        thread = BaseThread(
            name='fetch_browsed_assets_thread',
            target=self._fetch_versions,
            target_args=[self._entity_browser.entity],
        )
        thread.start()

    def _recursive_get_descendant_ids(self, context):
        result = [context['id']]
        for child in context['children']:
            if child.entity_type != "Task":
                result.extend(self._recursive_get_descendant_ids(child))
        return result

    def _fetch_versions(self, context):
        '''Search ftrack for versions beneath the given *context_id*'''
        print(
            '@@@ AssemblerBrowserWidget::_fetch_versions({})'.format(context)
        )
        # Build list of parent ID's
        parent_ids = self._recursive_get_descendant_ids(context)
        self._tail = 0  # The current fetch position
        while True:
            versions = self.session.query(
                'select id,task,version from AssetVersion where task.parent.id in '
                '({0}) or task.id in ({0}) offset {1} limit {2}'.format(
                    ','.join(
                        [
                            '"{}"'.format(context_id)
                            for context_id in parent_ids
                        ]
                    ),
                    self._tail,
                    self._limit,
                )
            ).all()
            if len(versions) == 0:
                # We are done
                self.allVersionsFetched.emit()
                break

            components = self.extract_components(
                versions,
                include_unloadable=self._cb_show_non_compatible.isChecked(),
            )

            self.componentsFetched.emit(components)

            self._tail += len(versions)

    def _on_components_fetched(self, components):
        '''A chunk of versions has been obtained, filter > give setup and add to list'''
        # Will trigger list to be rebuilt.
        self.model.insertRows(self.model.rowCount(), components)

        self.update()

    def _on_all_versions_fetched(self):
        self._busy_widget.stop()
        self._busy_widget.setVisible(False)

        if self.model.rowCount() == 0:
            l = QtWidgets.QLabel('<html><i>No assets found!</i></html>')
            l.setObjectName("gray-darker")
            self.scroll.setWidget(center_widget(l))
            self._label_info.setText('No assets found')

    def update(self):
        '''Update UI on new fetched components'''
        if self.model.rowCount() > 0:
            self._label_info.setText(
                'Listing {} asset{}'.format(
                    self.model.rowCount(),
                    's' if self.model.rowCount() > 1 else '',
                )
            )

        self._assembler_client.run_button_no_load.setEnabled(
            self._loadable_count > 0
        )
        self._assembler_client.run_button.setEnabled(self._loadable_count > 0)

    def _on_search(self, text):
        if self._component_list:
            self._component_list.on_search(text)


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
        self.selection_updated.emit(self.selection())

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
            if index == 0:
                set_property(component_widget, 'first', 'true')
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
        self.prev_search_text = None
        self._component_widgets = []
        super(BrowserListWidget, self).__init__(
            assembler_widget, parent=parent
        )

    def build(self):
        super(BrowserListWidget, self).build()
        self.layout().addWidget(QtWidgets.QLabel(), 100)

    def post_build(self):
        super(BrowserListWidget, self).post_build()
        self.model.rowsInserted.connect(self._on_components_added)

    def _on_components_added(self, model, first, last):
        '''Add components recently added from model to list.'''
        for row in range(first, last + 1):
            index = self.model.createIndex(row, 0, self.model)

            (component, definitions) = self.model.data(index)

            # Append component accordion

            component_widget = self._asset_widget_class(
                index, self._assembler_widget, self.model.event_manager
            )
            if row == 0:
                set_property(component_widget, 'first', 'true')
            component_widget.set_component_and_definitions(
                component, definitions
            )
            self.layout().insertWidget(
                self.layout().count() - 1, component_widget
            )

            component_widget.clicked.connect(
                partial(self.asset_clicked, component_widget)
            )
            self._component_widgets.append(component_widget)

        self.selection_updated.emit(self.selection())

    def refresh(self, search_text):
        '''Update visibility based on search'''
        for component_widget in self._component_widgets:
            component_widget.setVisible(
                len(search_text) == 0 or component_widget.matches(search_text)
            )

    def on_search(self, text):
        if text != self.prev_search_text:
            self.refresh(text.lower())
            self.prev_search_text = text


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
        self._version_nr_widget = QtWidgets.QLabel()
        return self._version_nr_widget

    def set_version(self, version_nr):
        self._version_nr_widget.setText('v{}  '.format(str(version_nr)))

    def set_latest_version(self, is_latest_version):
        color = '#935BA2' if is_latest_version else '#FFBA5C'
        self._version_nr_widget.setStyleSheet(
            'color: {}; font-weight: bold;'.format(color)
        )


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
        return 32

    def get_ident_widget(self):
        '''Asset name and component name.file_type'''
        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())
        widget.layout().setContentsMargins(0, 0, 0, 0)
        widget.layout().setSpacing(0)

        # Add context path, relative to browser context
        self._path_widget = QtWidgets.QLabel()
        self._path_widget.setObjectName("gray-darker")

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

        lower_widget.layout().addWidget(QtWidgets.QLabel(), 100)

        widget.layout().addWidget(lower_widget)

        return widget

    def get_version_widget(self):
        self._version_nr_widget = AssemblerVersionComboBox(self.session)
        self._version_nr_widget.currentIndexChanged.connect(
            self._on_version_changed
        )
        return self._version_nr_widget

    def set_version(self, version_nr):
        pass

    def set_latest_version(self, is_latest_version):
        color = '#935BA2' if is_latest_version else '#FFBA5C'
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
        self._path_widget.setText(' / '.join(parent_path[index:]))
        self._version_nr_widget.set_context_id(self._context_id)
        self._version_nr_widget.set_asset_entity(component['version']['asset'])

        self.__last_compatible_version = component['version']

    def _on_version_changed(self, currentIndex):
        print(
            '@@@ BrowsedComponentWidget::_on_version_changed({})'.format(
                currentIndex
            )
        )

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
