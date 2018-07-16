import os
import sys
import logging
from QtExt import QtWidgets, QtGui, QtCore

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
            raise RuntimeError('Invalid arguments')

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


class FtrackReBuildServerTrackDialog(QtWidgets.QDialog, FtrackBase):
    excluded_component_names = ['ftrackreview-mp4', 'thumbnail']

    def __init__(self, selection, parent=None):
        self._result_data = {}

        if not parent:
            parent = hiero.ui.mainWindow()

        super(FtrackReBuildServerTrackDialog, self).__init__(parent)
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

        self._window_title = 'Rebuild Track from server tasks'
        self.setWindowTitle(self._window_title)
        # self.setWindowIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))

        self.setSizeGripEnabled(True)

        layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        self._tracknameField = QtWidgets.QLineEdit(BuildTrack.ProjectTrackNameDefault(selection))
        self._tracknameField.setToolTip('Name of new track')
        formLayout.addRow('Track name:', self._tracknameField)

        self.tasks_combobox = QtWidgets.QComboBox()
        formLayout.addRow('Task type:', self.tasks_combobox)

        self.asset_type_combobox = QtWidgets.QComboBox()

        formLayout.addRow('Asset type:', self.asset_type_combobox)

        self.asset_status_combobox = QtWidgets.QComboBox()
        formLayout.addRow('Asset Status:', self.asset_status_combobox)

        self.component_combobox = QtWidgets.QComboBox()
        formLayout.addRow('Component name:', self.component_combobox)

        layout.addLayout(formLayout)

        # Add the standard ok/cancel buttons, default to ok.
        self._buttonbox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Build")
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDisabled(True)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setAutoDefault(True)
        self._buttonbox.accepted.connect(self.acceptTest)
        self._buttonbox.rejected.connect(self.reject)
        layout.addWidget(self._buttonbox)

        self.setLayout(layout)

        # populate data
        self.populate_tasks()
        self.populate_asset_types()
        self.populate_components()
        self.populate_asset_statuses()

        # connect signals
        self.tasks_combobox.currentIndexChanged.connect(self.get_components)
        self.asset_type_combobox.currentIndexChanged.connect(self.get_components)
        self.component_combobox.currentIndexChanged.connect(self.get_components)
        self.asset_status_combobox.currentIndexChanged.connect(self.get_components)

        # force ui to refresh
        self.get_components()


    @staticmethod
    def common_items(items):
        if not items:
            return []
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
        asset_status = self.asset_status_combobox.currentText()

        if not all([task_name, asset_type_name, component_name]):
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

            if asset_status != '- ANY -':
                query += ' and version.status.name is "{}"'.format(asset_status)

            final_component = self.session.query(query
            ).first()

            if not final_component:
                continue

            self._result_data[taskItem] = final_component['id']

        # Update window title with the amount of clips found matching the filters
        new_title = self._window_title + ' - ({} clips found)'.format(len(self._result_data))
        self.setWindowTitle(new_title)

        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDisabled(not bool(len(self._result_data)))

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

            # We should filter components based on the processor task names: [Foundry] Ticket: 38929
            # For now let's simply filter the one which are not acceptable
            all_component_names.append(
                [component['name'] for component in components if component['name'] not in self.excluded_component_names]
            )

        common_components = self.common_items(all_component_names)
        for name in sorted(common_components):
            self.component_combobox.addItem(name)

    def populate_asset_statuses(self):
        statuses = self.session.query('Status').all()
        self.asset_status_combobox.addItem('- ANY -')
        for status in statuses:
            self.asset_status_combobox.addItem(status['name'])


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
        for name in sorted(common_tasks):
            self.tasks_combobox.addItem(name)


class FtrackReBuildServerTrackAction(BuildTrackActionBase, FtrackBase):
    def __init__(self):
        super(FtrackReBuildServerTrackAction, self).__init__('Rebuild from ftrack')
        self.trackFinder = FtrackTrackFinderByNameWithDialog(self)
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))

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
        return [path.split()[0]]

    def getExpectedRange(self, trackItem):

        component_id = self._track_data.get(trackItem)
        if not component_id:
            return 0, 0, None, None, 0

        component = self.session.get('Component', component_id)
        shot = component['version']['asset']['parent']
        attributes = shot['custom_attributes']

        offset = 0
        start = int(attributes.get('fstart', 0))
        duration = int(attributes.get('fend', 0)) - start
        starthandle, endhandle = 0, 0

        result = (start, duration, starthandle, endhandle, offset)
        return result

    def trackName(self):
        return self._trackName

    def configure(self, project, selection):

        # Check the preferences for whether the built clips should be comp clips in the
        # case that the export being built from was a Nuke Shot export.
        settings = hiero.core.ApplicationSettings()

        dialog = FtrackReBuildServerTrackDialog(selection)
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


        if not self.configure(project, selection):
          return

        self._buildTrack(selection, sequence, project)

        if self._errors:
          msgBox = QtWidgets.QMessageBox(hiero.ui.mainWindow())
          msgBox.setWindowTitle('Rebuild Media Track')
          msgBox.setText('There were problems building the track.')
          msgBox.setDetailedText( '\n'.join(self._errors) )
          msgBox.exec_()
          self._errors = []

    def add_ftrack_build_tag(self, clip, originalTrackItem):
        # add tags to clips
        component_id = self._track_data.get(originalTrackItem)
        if not component_id:
            return

        component = self.session.get('Component', component_id)
        version = component['version']

        tag = hiero.core.Tag(
            'ftrack-reference-{0}'.format(component['name']),
            ':/ftrack/image/default/ftrackLogoColor',
            False
        )
        tag.metadata().setValue('tag.component_id', component['id'])
        tag.metadata().setValue('tag.version_id', version['id'])
        tag.metadata().setValue('tag.provider', 'ftrack')
        # tag.setVisible(False)
        clip.addTag(tag)

    def _buildTrackItem(self, name, clip, originalTrackItem, expectedStartTime, expectedDuration, expectedStartHandle,
                        expectedEndHandle, expectedOffset):
        # Create the item
        self.logger.info('_buildTrackItem {0}'.format(name))
        trackItem = hiero.core.TrackItem(name, hiero.core.TrackItem.kVideo)
        trackItem.setSource(clip)

        # Copy the timeline in/out
        trackItem.setTimelineIn(originalTrackItem.timelineIn())
        trackItem.setTimelineOut(originalTrackItem.timelineOut())

        # Calculate the source in/out times.  Try to match frame numbers, compensating for handles etc.
        mediaSource = clip.mediaSource()

        originalClip = originalTrackItem.source()
        originalMediaSource = originalClip.mediaSource()

        # If source durations match, and there were no retimes, then the whole clip was exported, and we should use the same source in/out
        # as the original.  The correct handles are not being stored in the tag in this case.
        fullClipExported = (originalMediaSource.duration() == mediaSource.duration())

        if fullClipExported:
            sourceIn = originalTrackItem.sourceIn()
            sourceOut = originalTrackItem.sourceOut()

        # Otherwise try to use the export handles and retime info to determine the correct source in/out
        else:
            # On the timeline, the first frame of video files is always 0.  Reset the start time
            isVideoFile = hiero.core.isVideoFileExtension(os.path.splitext(mediaSource.fileinfos()[0].filename())[1])
            if isVideoFile:
                expectedStartTime = 0

            sourceIn = expectedStartTime - mediaSource.startTime()
            if expectedStartHandle is not None:
                sourceIn += expectedStartHandle

            # First add the abs src duration to get the source out
            sourceOut = sourceIn + abs(originalTrackItem.sourceOut() - originalTrackItem.sourceIn())

            # Then, for a negative retime, src in/out need to be reversed
            if originalTrackItem.playbackSpeed() < 0.0:
                sourceIn, sourceOut = sourceOut, sourceIn

        trackItem.setSourceIn(sourceIn)
        trackItem.setSourceOut(sourceOut)
        self.add_ftrack_build_tag(clip, originalTrackItem)
        return trackItem

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
        self._action_rebuild_from_server = FtrackReBuildServerTrackAction()
        self.addAction(self._action_rebuild_from_server)

    def eventHandler(self, event):
        # Check if this actions are not to be enabled
        restricted = []
        if hasattr(event, 'restricted'):
          restricted = getattr(event, 'restricted');
        if 'buildExternalMediaTrack' in restricted:
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

        self._action_rebuild_from_server.setEnabled(len(selection)>0)

        event.menu.addMenu(self)
