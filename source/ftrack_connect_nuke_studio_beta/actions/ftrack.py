import logging
import collections
from QtExt import QtWidgets, QtGui, QtCore


from ftrack_connect_nuke_studio_beta.base import FtrackBase

import hiero

from hiero.ui.BuildExternalMediaTrack import (
    BuildTrack,
    BuildTrackActionBase,
    BuildTrackFromExportTagAction,
    BuildTrackFromExportTagDialog,
    BuildExternalMediaTrackAction,
    BuildExternalMediaTrackDialog,
    TrackFinderByNameWithDialog
)

registry = hiero.core.taskRegistry


class FtrackBuildServerTrackDialog(QtWidgets.QDialog, FtrackBase):

    def __init__(self, selection, parent=None):
        if not parent:
            parent = hiero.ui.mainWindow()

        super(FtrackBuildServerTrackDialog, self).__init__(parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

        num_tasks = registry.numTasks()
        self._ftrack_tasks = [registry.taskName(index) for index in range(num_tasks)]

        self.logger.info(self._ftrack_tasks)
        self._selection = selection

        if self._selection:
            self.project = self.itemProject(self._selection[0])

        self.setWindowTitle("Build Track From server tasks")
        self.setSizeGripEnabled(True)

        layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        self._tracknameField = QtWidgets.QLineEdit(BuildTrack.ProjectTrackNameDefault(selection))
        self._tracknameField.setToolTip("Name of new track")
        formLayout.addRow("Track Name:", self._tracknameField)

        self.tasks_combobox = QtWidgets.QComboBox()
        self.tasks_combobox.currentIndexChanged.connect(self.get_components)
        formLayout.addRow("Task:", self.tasks_combobox)

        self.asset_type_combobox = QtWidgets.QComboBox()
        self.asset_type_combobox.currentIndexChanged.connect(self.get_components)

        formLayout.addRow("Asset Type:", self.asset_type_combobox)

        self.component_combobox = QtWidgets.QComboBox()
        self.component_combobox.currentIndexChanged.connect(self.get_components)
        formLayout.addRow("Component :", self.component_combobox)

        layout.addLayout(formLayout)
        self.setLayout(layout)

        # build button

        self.build_button = QtWidgets.QPushButton('Build')
        self.build_button.clicked.connect(self.build_tracks)
        formLayout.addRow("Build Track", self.build_button)

        # populate data
        self.populate_tasks()
        self.populate_asset_types()
        self.populate_components()


    @staticmethod
    def common_items(items):
        return set.intersection(*map(set, items))

    @property
    def parsed_selection(self):
        results = []
        project_name = self.project.name()
        for trackItem in self._selection:
            if not isinstance(trackItem, hiero.core.EffectTrackItem):
                sequence, shot = trackItem.name().split('_') # TODO
                results.append((project_name, sequence, shot))

        self.logger.info(results)

        return results

    @property
    def trackName(self):
        return str(self._tracknameField.text())

    def itemProject(self, item):
        if hasattr(item, 'project'):
            return item.project()
        elif hasattr(item, 'parent'):
            return self.itemProject(item.parent())
        else:
            return None

    def build_tracks(self):
        components = self.get_components()
        paths = {}
        for component in components:
            clipname = component['metadata'].get('clip_name')
            component_avaialble = self.session.pick_location(component)

            if not component_avaialble or not clipname:
                continue

            path = self.ftrack_location.get_filesystem_path(component)
            paths[clipname] = path

    def get_components(self, index=None):
        all_components = []
        task = self.tasks_combobox.currentText()
        asset_type = self.asset_type_combobox.currentText()
        component = self.component_combobox.currentText()

        if not all([task, asset_type, component]):
            self.build_button.setDisabled(not bool(all_components))
            return all_components

        for (project, sequence, shot) in self.parsed_selection:

            query = (
                'Component where name is {} '  # component name 
                'and version.asset.type.name is "{}" '  # asset type
                'and version.task.name is "{}" '  # task name
                'and version.asset.parent.name is "{}" '  # shot
                'and version.asset.parent.parent.name is "{}" '  # sequence
                'and version.asset.parent.project.name is "{}"'  # project
                ''.format(component, asset_type, task, shot, sequence, project)
            )
            self.logger.info('query: {0}'.format(query))

            final_component = self.session.query(query
            ).first()

            if not final_component:
                continue

            all_components.append(final_component)

        # if no result is found, disable builds
        self.build_button.setDisabled(not bool(all_components))
        self.logger.info(all_components)
        return all_components


    def populate_components(self):
        all_component_names = []
        for (project, sequence, shot) in self.parsed_selection:
            components = self.session.query(
                'select name, version.asset.parent.name, version.asset.parent.parent.name from Component '
                'where version.asset.parent.name is "{}" and version.asset.parent.parent.name is "{}" and version.asset.parent.project.name is "{}"'.format(
                    shot, sequence, project
                )
            ).all()

            if not components:
                continue

            # WE SHOULD FILTER HERE BASED ON REGISTERED FTRACK TASKS.
            all_component_names.append([component['name'] for component in components])

        common_components = self.common_items(all_component_names)
        self.logger.info('component_combobox : {}'.format(common_components))
        for name in sorted(common_components):
            self.component_combobox.addItem(name)

    def populate_asset_types(self):
        all_asset_types_names = []
        for (project, sequence, shot) in self.parsed_selection:
            assets = self.session.query(
                'select type, name, parent.name, parent.parent.name from Asset '
                'where parent.name is "{}" and parent.parent.name is "{}" and parent.project.name is "{}"'.format(
                    shot, sequence, project
                )
            ).all()

            if not assets:
                continue

            all_asset_types_names.append([asset['type']['name'] for asset in assets])
        common_asset_types = self.common_items(all_asset_types_names)
        self.logger.info('common_asset_types : {}'.format(common_asset_types))
        for name in sorted(common_asset_types):
            self.asset_type_combobox.addItem(name)

    def populate_tasks(self):
        all_tasks=[]
        for (project, sequence, shot) in self.parsed_selection:
            tasks = self.session.query(
                'select name, parent.name, parent.parent.name from Task '
                'where parent.name is "{}" and parent.parent.name is "{}" and project.name is "{}"'.format(
                    shot, sequence, project
                )
            ).all()

            if not tasks:
                continue

            all_tasks.append([task['name'] for task in tasks])
        common_tasks = self.common_items(all_tasks)
        self.logger.info('common_tasks : {}'.format(common_tasks))
        for name in sorted(common_tasks):
            self.tasks_combobox.addItem(name)


class FtracBuildServerTrackAction(BuildTrackActionBase):
    def __init__(self):
        super(FtracBuildServerTrackAction, self).__init__("From Ftrack Server")

    def configure(self, project, selection):

        # Check the preferences for whether the built clips should be comp clips in the
        # case that the export being built from was a Nuke Shot export.
        settings = hiero.core.ApplicationSettings()

        dialog = FtrackBuildServerTrackDialog(selection)
        if dialog.exec_():
          self._trackName = dialog.trackName()
          return True
        else:
          return False


# =========================================================================================
# Main Menu

class FtrackBuildTrack(BuildTrack):

    def __init__(self):
        QtWidgets.QMenu.__init__(self, 'Build Track', None)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)
        hiero.core.events.registerInterest('kShowContextMenu/kTimeline', self.eventHandler)
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))
        self._actionServer = FtracBuildServerTrackAction()
        self.addAction(self._actionServer)

    def eventHandler(self, event):
        # Check if this actions are not to be enabled
        restricted = []
        if hasattr(event, 'restricted'):
          restricted = getattr(event, 'restricted');
        if "buildExternalMediaTrack" in restricted:
          return

        if not hasattr(event.sender, 'selection'):
          # Something has gone wrong, we shouldn't only be here if raised
          # by the timeline view which will give a selection.
          return

        selection = event.sender.selection()

        # We don't need this action if a user has right-clicked on a Track header
        trackSelection = [item for item in selection if isinstance(item, (hiero.core.VideoTrack,hiero.core.AudioTrack))]
        if len(trackSelection)>0:
          return

        #filter out the Audio Tracks
        selection = [ item for item in selection if isinstance(item.parent(), hiero.core.VideoTrack) ]

        if selection is None:
          selection = () # We disable on empty selection.
        self.setEnabled(len(selection)>0)

        event.menu.addMenu(self)
