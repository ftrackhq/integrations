# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from qtpy import QtWidgets, QtCore

from ftrack_connect_pipeline.ui.widget.entity_path import EntityPath
import ftrack_connect_pipeline.ui.widget.entity_browser as entityBrowser


class ContextSelector(QtWidgets.QWidget):
    entityChanged = QtCore.Signal(object)

    @property
    def entity(self):
        return self._entity

    def __init__(self, session, currentEntity=None, parent=None):
        '''Initialise ContextSelector widget with the *currentEntity* and
        *parent* widget.
        '''
        super(ContextSelector, self).__init__(parent=parent)
        self._entity = currentEntity
        self.entityBrowser = entityBrowser.EntityBrowser(session)
        self.entityBrowser.setMinimumWidth(600)
        self.entityPath = EntityPath()
        self.entityBrowseButton = QtWidgets.QPushButton('Browse')

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

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
        self.setEntity(currentEntity)

    def reset(self, entity=None):
        '''reset browser to the given *entity* or the default one'''
        currentEntity = entity or self._entity
        self.entityPath.setEntity(currentEntity)
        self.setEntity(currentEntity)

    def setEntity(self, entity):
        '''Set the *entity* for the view.'''
        if not entity:
            return
        self._entity = entity
        self.entityChanged.emit(entity)

    def _onEntityBrowseButtonClicked(self):
        '''Handle entity browse button clicked.'''
        # Ensure browser points to parent of currently selected entity.
        if self._entity is not None:
            location = []
            parent = self._entity['parent']

            location.append(self._entity['id'])
            if parent:
                location.append(parent['id'])

            while parent:
                parent = parent['parent']
                if parent:
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
            self.entityBrowser.acceptButton.setDisabled(False)
