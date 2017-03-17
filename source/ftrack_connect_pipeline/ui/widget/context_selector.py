# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from QtExt import QtWidgets
from QtExt import QtCore
from QtExt import QtGui

import ftrack_connect_pipeline.ui.model.entity_tree
import ftrack_connect_pipeline.ui.widget.overlay

from ftrack_connect_pipeline import util


def _get_entity_parents(entity):
    '''Return the list of ancestors of the providede *entity*'''
    parents = [entity]
    parent = entity['parent']
    parents.append(parent)
    while parent:
        parent = parent['parent']
        if parent:
            parents.append(parent)
    parents.reverse()
    return parents


class EntityBrowser(QtWidgets.QDialog):
    '''Entity browser.'''

    #: Signal when location changed.
    locationChanged = QtCore.Signal()

    #: Signal when selection changes. Pass new selection.
    selectionChanged = QtCore.Signal(object)

    def __init__(self, root=None, parent=None):
        '''Initialise browser with *root* entity.

        Use an empty *root* to start with list of projects.

        *parent* is the optional owner of this UI element.

        '''
        super(EntityBrowser, self).__init__(parent=parent)
        self._root = root
        self._selected = []
        self._updatingNavigationBar = False

        self._session = util.get_session()

        self._construct()
        self._postConstruction()

    def _construct(self):
        '''Construct widget.'''
        self.setLayout(QtWidgets.QVBoxLayout())

        self.headerLayout = QtWidgets.QHBoxLayout()

        self.navigationBar = QtWidgets.QTabBar()
        self.navigationBar.setExpanding(False)
        self.navigationBar.setDrawBase(False)
        self.headerLayout.addWidget(self.navigationBar, stretch=1)

        self.navigateUpButton = QtWidgets.QToolButton()
        self.navigateUpButton.setObjectName('entity-browser-up-button')
        self.navigateUpButton.setIcon(
            QtGui.QIcon(':ftrack/image/light/upArrow')
        )
        self.navigateUpButton.setToolTip('Navigate up a level.')
        self.headerLayout.addWidget(self.navigateUpButton)

        self.reloadButton = QtWidgets.QToolButton()
        self.reloadButton.setObjectName('entity-browser-reload-button')

        self.reloadButton.setIcon(
            QtGui.QIcon(':ftrack/image/light/reload')
        )
        self.reloadButton.setToolTip('Reload listing from server.')
        self.headerLayout.addWidget(self.reloadButton)

        self.layout().addLayout(self.headerLayout)

        self.contentSplitter = QtWidgets.QSplitter()

        self.bookmarksList = QtWidgets.QListView()
        self.contentSplitter.addWidget(self.bookmarksList)

        self.view = QtWidgets.QTableView()
        self.view.setSelectionBehavior(self.view.SelectRows)
        self.view.setSelectionMode(self.view.SingleSelection)
        self.view.verticalHeader().hide()

        self.contentSplitter.addWidget(self.view)

        proxy = ftrack_connect_pipeline.ui.model.entity_tree.EntityTreeProxyModel(self)
        model = ftrack_connect_pipeline.ui.model.entity_tree.EntityTreeModel(
            root=ftrack_connect_pipeline.ui.model.entity_tree.ItemFactory(
                self._session, self._root
            ),
            parent=self
        )
        proxy.setSourceModel(model)
        proxy.setDynamicSortFilter(True)

        self.view.setModel(proxy)
        self.view.setSortingEnabled(True)

        self.contentSplitter.setStretchFactor(1, 1)
        self.layout().addWidget(self.contentSplitter)

        self.footerLayout = QtWidgets.QHBoxLayout()
        self.footerLayout.addStretch(1)

        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.footerLayout.addWidget(self.cancelButton)

        self.acceptButton = QtWidgets.QPushButton('Choose')
        self.footerLayout.addWidget(self.acceptButton)

        self.layout().addLayout(self.footerLayout)

        self.overlay = ftrack_connect_pipeline.ui.widget.overlay.BusyOverlay(
            self.view, message='Loading'
        )

    def _postConstruction(self):
        '''Perform post-construction operations.'''
        self.setWindowTitle('ftrack browser')
        self.view.sortByColumn(0, QtCore.Qt.AscendingOrder)

        # TODO: Remove once bookmarks widget implemented.
        self.bookmarksList.hide()

        self.acceptButton.setDefault(True)
        self.acceptButton.setDisabled(True)

        self.model.sourceModel().loadStarted.connect(self._onLoadStarted)
        self.model.sourceModel().loadEnded.connect(self._onLoadEnded)

        # Compatibility layer for PySide2/Qt5.
        # Please see: https://github.com/mottosso/Qt.py/issues/72
        # for more information.
        try:
            self.view.horizontalHeader().setResizeMode(
                QtWidgets.QHeaderView.ResizeToContents
            )
            self.view.horizontalHeader().setResizeMode(
                0, QtWidgets.QHeaderView.Stretch
            )
        except Exception:
            self.view.horizontalHeader().setSectionResizeMode(
                QtWidgets.QHeaderView.ResizeToContents
            )
            self.view.horizontalHeader().setSectionResizeMode(
                0, QtWidgets.QHeaderView.Stretch
            )

        self.acceptButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.navigationBar.currentChanged.connect(
            self._onSelectNavigationBarItem
        )
        self.navigateUpButton.clicked.connect(self._onNavigateUpButtonClicked)
        self.reloadButton.clicked.connect(self._onReloadButtonClicked)
        self.view.activated.connect(self._onActivateItem)

        selectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(self._onSelectionChanged)

        self._updateNavigationBar()

    @property
    def model(self):
        '''Return current model.'''
        return self.view.model()

    def selected(self):
        '''Return selected entities.'''
        return self._selected[:]

    def setLocation(self, location):
        '''Set location to *location*.

        *location* should be a list of entries representing the 'path' from the
        root of the model to the desired location.

        Each entry in the list should be an entity id.

        '''
        # Ensure root children loaded in order to begin search.
        rootIndex = self.model.index(-1, -1)
        if (
            self.model.hasChildren(rootIndex)
            and self.model.canFetchMore(rootIndex)
        ):
            self.model.fetchMore(rootIndex)

        # Search for matching entries by identity.
        role = self.model.sourceModel().IDENTITY_ROLE

        matchingIndex = rootIndex
        searchIndex = self.model.index(0, 0)
        for identity in location:
            matches = self.model.match(
                searchIndex, role, identity
            )
            if not matches:
                break

            matchingIndex = matches[0]
            if (
                self.model.hasChildren(matchingIndex)
                and self.model.canFetchMore(matchingIndex)
            ):
                self.model.fetchMore(matchingIndex)

            searchIndex = self.model.index(0, 0, parent=matchingIndex)

        else:
            self.setLocationFromIndex(matchingIndex)
            return

        raise ValueError('Could not match location {0!r}'.format(location))

    def getLocation(self):
        '''Return current location as list of entity ids from root.'''
        location = []
        item = self.model.item(self.view.rootIndex())
        while item is not None and item.entity != self._root:
            location.append(item.id)
            item = item.parent

        location.reverse()
        return location

    def setLocationFromIndex(self, index):
        '''Set location to *index*.'''
        if index is None:
            index = QtCore.QModelIndex()

        currentIndex = self.view.rootIndex()
        if index == currentIndex:
            return

        self.view.setRootIndex(index)
        self._updateNavigationBar()

        selectionModel = self.view.selectionModel()
        selectionModel.clearSelection()

        self.locationChanged.emit()

    def _onLoadStarted(self):
        '''Handle load started.'''
        self.reloadButton.setEnabled(False)
        self.overlay.show()

    def _onLoadEnded(self):
        '''Handle load ended.'''
        self.overlay.hide()
        self.reloadButton.setEnabled(True)

    def _updateNavigationBar(self):
        '''Update navigation bar.'''
        if self._updatingNavigationBar:
            return

        self._updatingNavigationBar = True

        # Clear all existing entries.
        for index in range(self.navigationBar.count(), -1, -1):
            self.navigationBar.removeTab(index)

        # Compute new entries.
        entries = []
        index = self.view.rootIndex()
        while index.isValid():
            item = self.model.item(index)
            entries.append(
                dict(icon=item.icon, label=item.name, index=index)
            )
            index = self.model.parent(index)

        item = self.model.root
        entries.append(
            dict(icon=item.icon, label=item.name, index=None)
        )

        entries.reverse()
        for entry in entries:
            tabIndex = self.navigationBar.addTab(entry['icon'], entry['label'])
            self.navigationBar.setTabData(tabIndex, entry['index'])
            self.navigationBar.setCurrentIndex(tabIndex)

        self._updatingNavigationBar = False

    def _onSelectNavigationBarItem(self, index):
        '''Handle selection of navigation bar item.'''
        if index < 0:
            return

        if self._updatingNavigationBar:
            return

        modelIndex = self.navigationBar.tabData(index)
        self.setLocationFromIndex(modelIndex)

    def _onActivateItem(self, index):
        '''Handle activation of item in listing.'''
        if self.model.hasChildren(index):
            self.setLocationFromIndex(index)

    def _onSelectionChanged(self, selected, deselected):
        '''Handle change of *selection*.'''
        del self._selected[:]
        seen = set()

        for index in selected.indexes():
            row = index.row()
            if row in seen:
                continue

            seen.add(row)

            item = self.model.item(index)
            if item:
                self._selected.append(item.entity)

        selected = self.selected()
        if selected:
            self.acceptButton.setEnabled(True)
        else:
            self.acceptButton.setEnabled(False)

        self.selectionChanged.emit(self.selected())

    def _onNavigateUpButtonClicked(self):
        '''Navigate up on button click.'''
        currentRootIndex = self.view.rootIndex()
        parent = self.model.parent(currentRootIndex)
        self.setLocationFromIndex(parent)

    def _onReloadButtonClicked(self):
        '''Reload current index on button click.'''
        currentRootIndex = self.view.rootIndex()
        self.model.reloadChildren(currentRootIndex)


class EntityPath(QtWidgets.QLabel):
    '''Entity path widget.'''

    path_ready = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Instantiate the entity path widget.'''
        super(EntityPath, self).__init__(*args, **kwargs)
        self.path_ready.connect(self.on_path_ready)

    @util.asynchronous
    def setEntity(self, entity):
        '''Set the *entity* for this widget.'''
        names = []
        session = entity.session
        parents = _get_entity_parents(entity)

        for entity in parents:
            if entity:
                if isinstance(entity, session.types['Project']):
                    names.append(entity['full_name'])
                else:
                    names.append(entity['name'])

        self.path_ready.emit(names)

    def on_path_ready(self, names):
        result = ' / '.join(names)
        result = 'Publish to: <b>{0}</b>'.format(result)
        self.setText(result)


class ContextSelector(QtWidgets.QFrame):
    '''Context browser with entity path field.'''

    entityChanged = QtCore.Signal(object)

    def __init__(self, currentEntity, parent=None):
        '''Initialise with the *currentEntity* and *parent* widget.'''
        super(ContextSelector, self).__init__(parent=parent)
        self.setObjectName('context-selector-widget')
        self._entity = currentEntity
        self.entityBrowser = EntityBrowser()
        self.entityBrowser.setMinimumWidth(600)
        self.entityPath = EntityPath()

        self.entityBrowseButton = QtWidgets.QPushButton('Change')
        self.entityBrowseButton.setFixedWidth(110)
        self.entityBrowseButton.setFixedHeight(35)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        self.setMinimumHeight(50)
        self.setLayout(layout)

        layout.addWidget(self.entityPath)
        layout.addWidget(self.entityBrowseButton)

        self.entityBrowseButton.clicked.connect(
            self._onEntityBrowseButtonClicked
        )
        self.entityChanged.connect(self.entityPath.setEntity)
        self.entityBrowser.selectionChanged.connect(
            self._onEntityBrowserSelectionChanged
        )
        self.setEntity(self._entity)

    def reset(self, entity=None):
        '''Reset browser to the given *entity* or the default one.'''
        currentEntity = entity or self._entity
        self.entityPath.setEntity(currentEntity)
        self.setEntity(currentEntity)

    def setEntity(self, entity):
        '''Set the *entity* for the view.'''
        self._entity = entity
        self.entityChanged.emit(entity)

    def _onEntityBrowseButtonClicked(self):
        '''Handle entity browse button clicked.'''
        # Ensure browser points to parent of currently selected entity.
        if self._entity is not None:
            location = []
            try:
                parents = _get_entity_parents(self._entity)
            except AttributeError:
                pass
            else:
                for parent in parents:
                    location.append(parent['id'])

            self.entityBrowser.setLocation(location)

        # Launch browser.
        if self.entityBrowser.exec_():
            selected = self.entityBrowser.selected()
            session = selected[0].session

            if selected:
                self.setEntity(session.get('Context', selected[0]['id']))
            else:
                self.setEntity(None)

    def _onEntityBrowserSelectionChanged(self, selection):
        '''Handle selection of entity in browser.'''
        self.entityBrowser.acceptButton.setDisabled(True)

        # Only allow single select.
        if len(selection) == 1:
            # Do not allow selection of projects.
            if selection[0].entity_type == 'Project':
                return

            self.entityBrowser.acceptButton.setDisabled(False)
