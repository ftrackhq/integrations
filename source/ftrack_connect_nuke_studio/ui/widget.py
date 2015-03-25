# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import hiero
import ftrack
from FnAssetAPI.ui.toolkit import QtGui


class Resolution(hiero.ui.FormatChooser):
    '''Wrap hiero widget for promoted qtDesigner one.'''
    pass


class Fps(QtGui.QComboBox):
    '''Extract fps from hiero and expose them.'''
    def __init__(self, parent=None):
        super(Fps, self).__init__(parent=parent)
        for fps in hiero.core.defaultFrameRates():
            if fps.is_integer():
                self.addItem(str(int(fps)))
            else:
                self.addItem(str(fps))


class Workflow(QtGui.QComboBox):
    '''Expose availble workflows from ftrack's server.'''
    def __init__(self, parent=None):
        super(Workflow, self).__init__(parent=parent)
        self._schema = ftrack.getProjectSchemes()
        for schemata in self._schema:
            self.addItem(schemata.get('name'))


class ProjectSelector(QtGui.QWidget):
    '''Create or select existing project.'''

    NEW_PROJECT = 'NEW_PROJECT'
    EXISTING_PROJECT = 'EXISTING_PROJECT'

    def __init__(self, parent=None):
        '''Instantiate the project options.'''
        super(ProjectSelector, self).__init__(parent=parent)

        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

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

        self.existing_project_label = QtGui.QLabel('Existing project')
        self.existing_project_selector = QtGui.QComboBox(parent=self)

        self.new_project_label = QtGui.QLabel('Project name')
        self.new_project_name_edit = QtGui.QLineEdit()

        editor_layout.addRow(
            self.existing_project_label, self.existing_project_selector
        )
        editor_layout.addRow(
            self.new_project_label,
            self.new_project_name_edit
        )

        self.layout().addLayout(radio_button_layout)
        self.layout().addLayout(editor_layout)

        self.new_project_radio_button.toggle()

    def get_new_name(self):
        '''Return name for new project.'''
        return self.new_project_name_edit.text()

    def _on_new_project_toggled(self):
        '''Handle new project toggle event.'''
        self.existing_project_selector.hide()
        self.existing_project_label.hide()

        self.new_project_name_edit.show()
        self.new_project_label.show()

    def _on_existing_project_toggled(self):
        '''Handle existing project toggle event.'''
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

    def select_existing_project(self, name):
        '''Select existing project with *name*.'''

        self._on_existing_project_toggled()

        index = self.existing_project_selector.findText(name)
        self.existing_project_selector.setCurrentIndex(index)
        self.existing_project_radio_button.setChecked(True)

        self.setDisabled(True)
