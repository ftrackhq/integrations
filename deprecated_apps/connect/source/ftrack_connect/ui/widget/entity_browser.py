# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
#             Copyright (c) 2014 Martin Pengelly-Phillips
# :notice: Derived from Riffle (https://github.com/4degrees/riffle)

import os

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import qtawesome as qta

import ftrack_connect.ui.model.entity_tree
import ftrack_connect.ui.widget.overlay


class EntityBrowser(QtWidgets.QDialog):
    '''Entity browser.'''

    #: Signal when location changed.
    locationChanged = QtCore.Signal()

    #: Signal when selection changes. Pass new selection.
    selectionChanged = QtCore.Signal(object)

    def __init__(self, session, root=None, parent=None):
        '''Initialise browser with *root* entity.

        Use an empty *root* to start with list of projects.

        *parent* is the optional owner of this UI element.

        '''
        super(EntityBrowser, self).__init__(parent=parent)
        self._root = root
        self._selected = []
        self._updatingNavigationBar = False

        self._session = session

        self._construct()
        self._postConstruction()

    def _construct(self):
        '''Construct widget.'''
        self.setLayout(QtWidgets.QVBoxLayout())

        self.headerLayout = QtWidgets.QHBoxLayout()

        self.navigationBar = QtWidgets.QTabBar()
        self.navigationBar.setIconSize(QtCore.QSize(self.size() / 2))
        self.navigationBar.setExpanding(False)
        self.navigationBar.setDrawBase(False)
        self.headerLayout.addWidget(self.navigationBar, stretch=1)

        up_button = qta.icon('mdi.chevron-up')
        self.navigateUpButton = QtWidgets.QToolButton()
        self.navigateUpButton.setIcon(up_button)

        self.navigateUpButton.setObjectName('entity-browser-up-button')
        self.navigateUpButton.setToolTip('Navigate up a level.')
        self.headerLayout.addWidget(self.navigateUpButton)

        reload_button = qta.icon('mdi6.sync')
        self.reloadButton = QtWidgets.QToolButton()
        self.reloadButton.setIcon(reload_button)
        self.reloadButton.setObjectName('entity-browser-reload-button')
        self.reloadButton.setToolTip('Reload listing from server.')
        self.headerLayout.addWidget(self.reloadButton)

        self.layout().addLayout(self.headerLayout)

        self.contentSplitter = QtWidgets.QSplitter()

        self.bookmarksList = QtWidgets.QListView()
        self.contentSplitter.addWidget(self.bookmarksList)

        self.view = QtWidgets.QTableView()
        self.view.setSelectionBehavior(self.view.SelectionBehavior.SelectRows)
        self.view.setSelectionMode(self.view.SelectionMode.SingleSelection)
        self.view.verticalHeader().hide()

        self.contentSplitter.addWidget(self.view)

        proxy = ftrack_connect.ui.model.entity_tree.EntityTreeProxyModel(self)
        model = ftrack_connect.ui.model.entity_tree.EntityTreeModel(
            root=ftrack_connect.ui.model.entity_tree.ItemFactory(
                self._session, self._root
            ),
            parent=self,
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

        self.overlay = ftrack_connect.ui.widget.overlay.BusyOverlay(
            self.view, message='Loading'
        )

    def _postConstruction(self):
        '''Perform post-construction operations.'''
        self.setWindowTitle('ftrack browser')
        self.view.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)

        # TODO: Remove once bookmarks widget implemented.
        self.bookmarksList.hide()

        self.acceptButton.setDefault(True)
        self.acceptButton.setDisabled(True)

        self.model.sourceModel().loadStarted.connect(self._onLoadStarted)
        self.model.sourceModel().loadEnded.connect(self._onLoadEnded)

        self.view.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.view.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
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
        if self.model.hasChildren(rootIndex) and self.model.canFetchMore(
            rootIndex
        ):
            self.model.fetchMore(rootIndex)

        # Search for matching entries by identity.
        role = self.model.sourceModel().IDENTITY_ROLE

        matchingIndex = rootIndex
        searchIndex = self.model.index(0, 0)
        for identity in location:
            matches = self.model.match(searchIndex, role, identity)
            if not matches:
                break

            matchingIndex = matches[0]
            if self.model.hasChildren(
                matchingIndex
            ) and self.model.canFetchMore(matchingIndex):
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
            entries.append(dict(icon=item.icon, label=item.name, index=index))
            index = self.model.parent(index)

        item = self.model.root
        entries.append(dict(icon=item.icon, label=item.name, index=None))

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
