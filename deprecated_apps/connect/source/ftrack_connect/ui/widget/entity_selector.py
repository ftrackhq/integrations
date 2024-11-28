# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import qtawesome as qta

from ftrack_connect.ui.widget import entity_path as _entity_path
from ftrack_connect.ui.widget import entity_browser as _entity_browser


class ContextList(QtWidgets.QComboBox):
    # https://forum.qt.io/topic/14676/how-can-i-keep-a-qcombobox-from-changing-width-due-to-contents/15
    # force combo box to minimum size.

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return QtCore.QSize(
            50, QtWidgets.QComboBox.minimumSizeHint(self).height()
        )


class EntitySelector(QtWidgets.QStackedWidget):
    '''Entity selector widget.'''

    entityChanged = QtCore.Signal(object)

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session, parent=None):
        '''Instantiate the entity selector widget.'''
        super(EntitySelector, self).__init__(parent=parent)
        self._entity = None
        self._user_tasks = []
        self._session = session
        # Create widget used to select an entity.
        selectionWidget = QtWidgets.QFrame()
        selectionWidget.setLayout(QtWidgets.QHBoxLayout())
        selectionWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.insertWidget(0, selectionWidget)

        self.entityBrowser = _entity_browser.EntityBrowser(
            self.session, parent=self
        )
        self.entityBrowser.setMinimumSize(600, 400)
        self.entityBrowser.selectionChanged.connect(
            self._onEntityBrowserSelectionChanged
        )

        self.entityBrowseButton = QtWidgets.QPushButton('BROWSE')
        self.entityBrowseButton.setMaximumWidth(150)
        self.assignedContextSelector = ContextList()

        selectionWidget.layout().addWidget(self.assignedContextSelector)
        selectionWidget.layout().addWidget(self.entityBrowseButton)

        # Create widget used to present current selection.
        presentationWidget = QtWidgets.QFrame()
        presentationWidget.setLayout(QtWidgets.QHBoxLayout())
        presentationWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.insertWidget(1, presentationWidget)

        self.entityPath = _entity_path.EntityPath()
        presentationWidget.layout().addWidget(self.entityPath)
        cancel_button = qta.icon('ftrack.cancel')

        self.discardEntityButton = QtWidgets.QPushButton()
        self.discardEntityButton.setObjectName('primary')
        self.discardEntityButton.setIcon(cancel_button)

        self.discardEntityButton.setObjectName('entity-selector-remove-button')
        self.discardEntityButton.clicked.connect(
            self._onDiscardEntityButtonClicked
        )

        presentationWidget.layout().addWidget(self.discardEntityButton)

        self.entityChanged.connect(self.entityPath.setEntity)
        self.assignedContextSelector.currentIndexChanged.connect(
            self.updateEntityPath
        )

        self.entityChanged.connect(self._updateIndex)

        self.entityBrowseButton.clicked.connect(
            self._onEntityBrowseButtonClicked
        )
        assigned_tasks = self._fetch_user_tasks()

        if assigned_tasks:
            self.assignedContextSelector.setCurrentIndex(1)
        else:
            self._onDiscardEntityButtonClicked()

    def _getPath(self, entity):
        '''Return path to *entity*.'''
        path = [e['name'].strip() for e in entity.get('link', [])]
        return ' / '.join(path)

    def _fetch_user_tasks(self, task_number=10):
        '''Update assigned list.'''
        self._user_tasks = [None]  # add placeholder for fake label below
        self.assignedContextSelector.clear()
        self.assignedContextSelector.addItem(
            '- Select a task or browse. - ', None
        )

        assigned_tasks = self.session.query(
            'select project, priority, assignments.resource.username, link, status.name from Task '
            'where assignments any (resource.username = "{0}") and '
            'status.name not_in ("Omitted", "On Hold", "Completed") and project.status is "active" '
            'order by priority.sort '
            'limit {1}'.format(self.session.api_user, task_number)
        ).all()

        for task in assigned_tasks:
            self.assignedContextSelector.addItem(self._getPath(task), task)
            self._user_tasks.append(task)

        return assigned_tasks

    def updateEntityPath(self, index):
        entity = self.assignedContextSelector.itemData(
            index, QtCore.Qt.ItemDataRole.UserRole
        )
        self.setEntity(entity)

    def _updateIndex(self, entity):
        '''Update the widget when entity changes.'''
        if entity:
            self.setCurrentIndex(1)
        else:
            self.setCurrentIndex(0)

    def _onDiscardEntityButtonClicked(self):
        '''Handle discard entity button clicked.'''
        self.setEntity(None)
        self.assignedContextSelector.setCurrentIndex(0)
        self._fetch_user_tasks()

    def _onEntityBrowseButtonClicked(self):
        '''Handle entity browse button clicked.'''
        # Ensure browser points to parent of currently selected entity.
        if self._entity is not None:
            location = []
            try:
                parents = self._entity['ancestors']
            except AttributeError:
                pass
            else:
                for parent in parents:
                    location.append(parent['id'])

            location.reverse()
            self.entityBrowser.setLocation(location)

        # Launch browser.
        if self.entityBrowser.exec_():
            selected = self.entityBrowser.selected()
            if selected:
                self.setEntity(selected[0])
            else:
                self.setEntity(None)

    def _onEntityBrowserSelectionChanged(self, selection):
        '''Handle selection of entity in browser.'''
        self.entityBrowser.acceptButton.setDisabled(True)
        if len(selection) == 1:
            entity = selection[0]

            if self.isValidBrowseSelection(entity):
                self.entityBrowser.acceptButton.setDisabled(False)

    def setEntity(self, entity):
        '''Set the *entity* for the view.'''
        self._entity = entity
        self.entityChanged.emit(entity)

    def getEntity(self):
        '''Return current entity.'''
        return self._entity

    def isValidBrowseSelection(self, entity):
        '''Return True if selected *entity* is valid.'''
        return True

    def forceUpdate(self):
        '''Force the emission of the entityChanged event with the current entity.'''
        self.entityChanged.emit(self._entity)
