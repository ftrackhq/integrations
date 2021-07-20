# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack


from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo
import ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser as entityBrowser
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import Context


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
        self.session = session

        self.pre_build()
        self.build()
        self.post_build()

        self.setEntity(currentEntity)

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def build(self):
        self.thumbnail_widget = Context(self.session)
        self.thumbnail_widget.setMinimumWidth(50)
        self.thumbnail_widget.setMinimumHeight(50)
        self.thumbnail_widget.setMaximumWidth(150)
        self.thumbnail_widget.setMaximumHeight(150)

        self.entityBrowser = entityBrowser.EntityBrowser(self.session)
        self.entityBrowser.setMinimumWidth(600)

        self.entity_info = EntityInfo()
        self.entity_info.setMaximumHeight(100)

        self.entityBrowseButton = QtWidgets.QPushButton('Change')

        self.layout().addWidget(self.thumbnail_widget)
        self.layout().addWidget(self.entity_info)
        self.layout().addWidget(self.entityBrowseButton)

    def set_thumbnmail(self, entity):
        self.thumbnail_widget.load(entity['id'])

    def post_build(self):
        self.entityBrowseButton.clicked.connect(
            self._onEntityBrowseButtonClicked
        )
        self.entityChanged.connect(self.entity_info.setEntity)
        self.entityChanged.connect(self.set_thumbnmail)
        self.entityBrowser.selectionChanged.connect(
            self._onEntityBrowserSelectionChanged
        )
        self.setMaximumHeight(150)

    def reset(self, entity=None):
        '''reset browser to the given *entity* or the default one'''
        currentEntity = entity or self._entity
        self.entity_info.setEntity(currentEntity)
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
