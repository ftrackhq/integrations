# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from PySide import QtGui, QtCore
import logging

import ftrack


class ProjectSelector(QtGui.QWidget):
    '''Create or select existing project.'''

    project_selected = QtCore.Signal((object, object))

    NEW_PROJECT = 'NEW_PROJECT'
    EXISTING_PROJECT = 'EXISTING_PROJECT'

    def __init__(self, project_name='', parent=None):
        '''Instantiate the project options with optional *project_name*.'''
        super(ProjectSelector, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self._state = self.NEW_PROJECT
        self._entity = None
        self._hasEditedName = False
        self._projects = None

        radio_button_layout = QtGui.QHBoxLayout()
        radio_button_layout.setContentsMargins(0, 0, 0, 0)

        self.radio_button_label = QtGui.QLabel('Project')
        radio_button_layout.addWidget(self.radio_button_label)

        self.new_project_radio_button = QtGui.QRadioButton('Create new')
        self.new_project_radio_button.toggled.connect(
            self._on_new_project_toggled
        )

        radio_button_layout.addWidget(self.new_project_radio_button)

        self.existing_project_radio_button = QtGui.QRadioButton('Use existing')
        self.existing_project_radio_button.toggled.connect(
            self._on_existing_project_toggled
        )
        radio_button_layout.addWidget(self.existing_project_radio_button)

        editor_layout = QtGui.QFormLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)

        existing_project_layout = QtGui.QHBoxLayout()
        existing_project_layout.setContentsMargins(0, 0, 0, 0)

        self.existing_project_label = QtGui.QLabel('Existing project')
        self.existing_project_selector = QtGui.QComboBox(parent=self)

        self.existing_project_selector.currentIndexChanged.connect(
            self._on_existing_project_selected
        )

        new_project_layout = QtGui.QHBoxLayout()
        new_project_layout.setContentsMargins(0, 0, 0, 0)

        self.new_project_label = QtGui.QLabel('Enter manually')
        self.new_project_name_edit = QtGui.QLineEdit(project_name)

        self.new_project_name_edit.editingFinished.connect(
            self._on_new_project_changed
        )

        existing_project_layout.addWidget(
            self.existing_project_label
        )

        existing_project_layout.addWidget(
            self.existing_project_selector
        )

        new_project_layout.addWidget(
            self.new_project_label, stretch=1
        )
        new_project_layout.addWidget(
            self.new_project_name_edit, stretch=1
        )

        self.layout().addLayout(radio_button_layout)
        self.layout().addLayout(existing_project_layout)
        self.layout().addLayout(new_project_layout)

        self.new_project_radio_button.toggle()

    def get_state(self):
        '''Return current state.'''
        return self._state

    def set_state(self, state):
        '''Set current state.'''
        self._state = state

    def get_new_name(self):
        '''Return name for new project.'''
        return self.new_project_name_edit.text()

    def _on_new_project_changed(self):
        '''Handle text changed events.'''
        self.logger.debug('On new project changed:{0}'.format(self.get_new_name()))
        self.project_selected.emit(self.get_new_name(), self.NEW_PROJECT)

    def _on_existing_project_selected(self, index):
        '''Handle select events in project selector.'''
        project = self.existing_project_selector.itemData(index)
        self.logger.debug('On existing project selected: {0}'.format(project.getName()))

        self.project_selected.emit(project.getName(), self.EXISTING_PROJECT)

    def _on_new_project_toggled(self, toggled):
        '''Handle new project toggle event.'''

        if toggled:

            self.set_state(self.NEW_PROJECT)
            self.existing_project_selector.hide()
            self.existing_project_label.hide()

            self.new_project_name_edit.show()
            self.new_project_label.show()

            self.logger.debug('On new project toggled: {0}'.format(self.get_new_name()))

            self.project_selected.emit(self.get_new_name(), self.NEW_PROJECT)

    def _on_existing_project_toggled(self, toggled):
        '''Handle existing project toggle event.'''

        if toggled:
            self.set_state(self.EXISTING_PROJECT)
            self.new_project_name_edit.hide()
            self.new_project_label.hide()

            self.existing_project_selector.show()
            self.existing_project_label.show()

            if self._projects is None:
                self._projects = ftrack.getProjects()
                for project in self._projects:
                    self.existing_project_selector.addItem(
                        project.getName(), project
                    )

            self._on_existing_project_selected(
                self.existing_project_selector.currentIndex()
            )
