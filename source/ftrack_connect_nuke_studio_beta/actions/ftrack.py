import logging
import collections
from QtExt import QtWidgets, QtGui, QtCore
import foundry

from ftrack_connect_nuke_studio_beta.base import FtrackBase

import hiero

from hiero.ui.BuildExternalMediaTrack import (
    BuildTrack,
    BuildTrackActionBase,
    TrackFinderByNameWithDialog
)

registry = hiero.core.taskRegistry


class FtrackTrackFinderByNameWithDialog(TrackFinderByNameWithDialog):

    def findOrCreateTrackByName(self, sequence, trackName):
        """ Searches the sequence for a track with the given name.  If none are found,
            creates a new one. """
        # a track always has to have a name
        if not trackName or not sequence:
            raise RuntimeError("Invalid arguments")

        track = None
        isNewTrack = False
        # Look for existing track
        for existingtrack in sequence.videoTracks():
            if existingtrack.trackName() == trackName:
                # hiero.core.log.debug( "Track Already Exists  : " + trackName )
                track = existingtrack

        # No existing track. Create new video track
        if track is None:
            # hiero.core.log.debug( "Track Created : " + trackName )
            track = hiero.core.VideoTrack(str(trackName))
            sequence.addTrack(track)
            track.addTag(hiero.core.Tag(trackName, ':ftrack/image/default/ftrackLogoColor'))
            isNewTrack = True
        return track, isNewTrack


class FtrackBuildServerTrackDialog(QtWidgets.QDialog, FtrackBase):

    def __init__(self, selection, parent=None):
        self._result_data = {}

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
        formLayout.addRow("Task:", self.tasks_combobox)

        self.asset_type_combobox = QtWidgets.QComboBox()

        formLayout.addRow("Asset Type:", self.asset_type_combobox)

        self.component_combobox = QtWidgets.QComboBox()
        formLayout.addRow("Component :", self.component_combobox)

        layout.addLayout(formLayout)

        # Add the standard ok/cancel buttons, default to ok.
        self._buttonbox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Build")
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setAutoDefault(True)
        self._buttonbox.accepted.connect(self.acceptTest)
        self._buttonbox.rejected.connect(self.reject)
        layout.addWidget(self._buttonbox)

        self.setLayout(layout)

        # populate data
        self.populate_tasks()
        self.populate_asset_types()
        self.populate_components()

        # connect signals
        self.tasks_combobox.currentIndexChanged.connect(self.get_components)
        self.asset_type_combobox.currentIndexChanged.connect(self.get_components)
        self.component_combobox.currentIndexChanged.connect(self.get_components)



    @staticmethod
    def common_items(items):
        return set.intersection(*map(set, items))

    @property
    def parsed_selection(self):
        results = {}
        project_name = self.project.name()
        for trackItem in self._selection:
            if not isinstance(trackItem, hiero.core.EffectTrackItem):
                sequence, shot = trackItem.name().split('_') # TODO
                results[trackItem] = (project_name, sequence, shot)
        return results

    def trackName(self):
        return str(self._tracknameField.text())

    def itemProject(self, item):
        if hasattr(item, 'project'):
            return item.project()
        elif hasattr(item, 'parent'):
            return self.itemProject(item.parent())
        else:
            return None

    @property
    def data(self):
        return self._result_data

    def acceptTest(self):
        if self.trackName():
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self, "Build Track from server",
                "Please set track names",
                QtWidgets.QMessageBox.Ok
        )

    def get_components(self, index=None):
        self._result_data = {}
        task_name = self.tasks_combobox.currentText()
        asset_type_name = self.asset_type_combobox.currentText()
        component_name = self.component_combobox.currentText()

        if not all([task_name, asset_type_name, component_name]):
            self._buttonbox.setDisabled(True)
            return self._result_data

        for taskItem, (project, sequence, shot) in self.parsed_selection.items():

            query = (
                'Component where name is {} '  # component name 
                'and version.asset.type.name is "{}" '  # asset type
                'and version.task.name is "{}" '  # task name
                'and version.asset.parent.name is "{}" '  # shot
                'and version.asset.parent.parent.name is "{}" '  # sequence
                'and version.asset.parent.project.name is "{}"'  # project
                ''.format(component_name, asset_type_name, task_name, shot, sequence, project)
            )
            self.logger.info('query: {0}'.format(query))

            final_component = self.session.query(query
            ).first()

            if not final_component:
                continue

            self._result_data[taskItem] = final_component['id']

        self._buttonbox.setDisabled(not bool(len(self._result_data)))

    def populate_components(self):
        all_component_names = []
        for (project, sequence, shot) in self.parsed_selection.values():
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
        for (project, sequence, shot) in self.parsed_selection.values():
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
        for (project, sequence, shot) in self.parsed_selection.values():
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


class FtracBuildServerTrackAction(BuildTrackActionBase, FtrackBase):
    def __init__(self):
        super(FtracBuildServerTrackAction, self).__init__("From Ftrack Server")
        self.trackFinder = FtrackTrackFinderByNameWithDialog(self)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

    def getExternalFilePaths(self, trackItem):
        component_id = self._track_data.get(trackItem)
        if not component_id:
            return []

        component = self.session.get('Component', component_id)
        component_avaialble = self.session.pick_location(component)
        if not component_avaialble:
            return []

        path = self.ftrack_location.get_filesystem_path(component)

        self.logger.info('getExternalFilePaths for {} is {}'.format(trackItem, path))
        return [path.split()[0]]

    def getExpectedRange(self, trackItem):
        """ Override. Get expected range based on the original track item.
            Returns None for handles so that they are calculated based on the duration
            of the new media. """

        component_id = self._track_data.get(trackItem)
        if not component_id:
            # if there's no component we return data from the previous clip
            source = trackItem.source().mediaSource()
            start, duration = source.startTime(), source.duration()
            starthandle, endhandle = None, None
            offset = 0
            return (start, duration, starthandle, endhandle, offset)

        component = self.session.get('Component', component_id)
        shot = component['version']['asset']['parent']
        attributes = shot['custom_attributes']

        offset = 0
        start = attributes.get('fstart')
        duration = attributes.get('fend') - start
        starthandle, endhandle = None, None

        return (start, duration, starthandle, endhandle, offset)


    def trackName(self):
        return self._trackName

    def configure(self, project, selection):

        # Check the preferences for whether the built clips should be comp clips in the
        # case that the export being built from was a Nuke Shot export.
        settings = hiero.core.ApplicationSettings()

        dialog = FtrackBuildServerTrackDialog(selection)
        if dialog.exec_():
          self._trackName = dialog.trackName()
          self._track_data = dialog.data
          return True
        else:
          return False

    def doit(self):
        selection = self.getTrackItems()

        sequence = hiero.ui.activeView().sequence()
        project = sequence.project()

        self.logger.info('sequence: {}'.format(sequence))
        self.logger.info('project: {}'.format(project))

        if not self.configure(project, selection):
          return

        self._buildTrack(selection, sequence, project)

        if self._errors:
          msgBox = QtWidgets.QMessageBox(hiero.ui.mainWindow())
          msgBox.setWindowTitle("Build Media Track")
          msgBox.setText("There were problems building the track.")
          msgBox.setDetailedText( '\n'.join(self._errors) )
          msgBox.exec_()
          self._errors = []


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
