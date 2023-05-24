# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import logging
from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_nuke_studio.base import FtrackBase
from ftrack_connect_nuke_studio.overrides.version_scanner import add_ftrack_build_tag
from ftrack_connect_nuke_studio.template import get_project_template, match
import ftrack_connect_nuke_studio.exception

import hiero

from hiero.ui.BuildExternalMediaTrack import (
    BuildTrack,
    BuildTrackActionBase,
    TrackFinderByNameWithDialog
)

registry = hiero.core.taskRegistry

logger = logging.getLogger(
    __name__
)


class FtrackTrackFinderByNameWithDialog(TrackFinderByNameWithDialog):
    '''Track creation widget.'''

    def findOrCreateTrackByName(self, sequence, track_name):
        ''' Searches the *sequence* for a track with the given *track_name* .  If none are found,
            creates a new one. '''
        # a track always has to have a name
        if not track_name or not sequence:
            raise RuntimeError('Invalid arguments')

        track = None
        is_new_track = False
        # Look for existing track
        for existingtrack in sequence.videoTracks():
            if existingtrack.trackName() == track_name:
                track = existingtrack

        # No existing track. Create new video track
        if track is None:
            track = hiero.core.VideoTrack(str(track_name))
            sequence.addTrack(track)
            track.addTag(hiero.core.Tag(
                track_name, ':ftrack/image/default/ftrackLogoLight')
            )
            is_new_track = True
        return track, is_new_track


class FtrackReBuildServerTrackDialog(QtWidgets.QDialog, FtrackBase):
    '''Rebuild from server widget.'''
    excluded_component_names = ['ftrackreview-mp4', 'thumbnail']

    def __init__(self, selection, parent=None):
        ''' Initialise class with *selection* and *parent* widget. '''
        self._result_data = {}

        if not parent:
            parent = hiero.ui.mainWindow()

        super(FtrackReBuildServerTrackDialog, self).__init__(parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        num_tasks = registry.numTasks()
        self._ftrack_tasks = [registry.taskName(index) for index in range(num_tasks)]

        self._selection = selection

        if self._selection:
            self.project = self.item_project(self._selection[0])

        self._window_title = 'Build track from ftrack'
        self.setWindowTitle(self._window_title)
        # self.setWindowIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))

        self.setSizeGripEnabled(True)

        layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        self._tracknameField = QtWidgets.QLineEdit()
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
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText('Build')
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDisabled(True)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setAutoDefault(True)
        self._buttonbox.accepted.connect(self.accept_test)
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

        # set suggested track name
        self._tracknameField.setText(self.suggested_track_name)

        # force ui to refresh
        self.get_components()

    @property
    def suggested_track_name(self):
        task_name = self.tasks_combobox.currentText()
        component_name = self.component_combobox.currentText()
        status = self.asset_status_combobox.currentText().replace('-', '').strip()
        new_track_name = '{}-{}-{}'.format(task_name, component_name, status)
        return new_track_name.upper()

    @staticmethod
    def common_items(items):
        ''' Return a set with only common entities in *items*. '''
        if not items:
            return set()
        return set.intersection(*map(set, items))

    @property
    def parsed_selection(self):
        ''' Return a dictionary with the parsed TrackItem selection. '''
        results = {}
        project_name = self.project.name()
        project_template = get_project_template(self.project)

        project_id = os.getenv('FTRACK_CONTEXTID')
        ftrack_project = self.session.get('Project', project_id)

        if not project_template:
            raise ftrack_connect_nuke_studio.exception.TemplateError(
                'No template defined for project {}'.format(project_name)
        )

        for trackItem in self._selection:
            if isinstance(trackItem, (hiero.core.EffectTrackItem, hiero.core.Transition)):
                continue
            try:
                parsed_results = match(trackItem, project_template)
            except ftrack_connect_nuke_studio.exception.TemplateError:
                continue
            results[trackItem] = [ftrack_project['name']] + [result['name'] for result in parsed_results]

        return results

    def trackName(self):
        ''' Return the new track name. '''
        return str(self._tracknameField.text())

    def item_project(self, item):
        ''' Return the project from given *item*. '''
        if hasattr(item, 'project'):
            return item.project()
        elif hasattr(item, 'parent'):
            return self.item_project(item.parent())
        else:
            return None

    @property
    def data(self):
        ''' Return the the collected data from widget. '''
        return self._result_data

    def accept_test(self):
        ''' Check whether the widget can be triggered. '''
        if self.trackName():
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Build track from ftrack',
                'Please set track names',
                QtWidgets.QMessageBox.Ok
        )

    def _get_context_leafs(self, data):
        '''return the lower most context leaf for the given set of data'''
        results = []
        for datum in data:
            project = datum[0]
            first_parent = datum[1]
            query = 'name is "{}" and project.name is "{}"'.format(first_parent, project)
            for index, item in enumerate(datum[2:]):
                query = 'name is "{}" and parent[TypedContext] has ({})'.format(item, query)
            full_query = u'TypedContext where {}'.format(query)

            results.extend(self.session.query(full_query).all())

        return results

    def get_components(self, index=None):
        ''' Return all the found components. '''
        self._result_data = {}
        task_name = self.tasks_combobox.currentText()
        asset_type_name = self.asset_type_combobox.currentText()
        component_name = self.component_combobox.currentText()
        asset_status = self.asset_status_combobox.currentText()

        if not all([task_name, asset_type_name, component_name]):
            return self._result_data

        for taskItem, context in self.parsed_selection.items():

            context_leafs = self._get_context_leafs([context])
            for context_leaf in context_leafs:
                query = (
                    'Component where name is "{}" '  # component name 
                    'and version.asset.type.name is "{}" '  # asset type
                    'and version.task.name is "{}" '  # task name
                    'and version.asset.parent.id is "{}" '  # shot
                    ''.format(component_name, asset_type_name, task_name,context_leaf['id'])
                )

                if asset_status != '- ANY -':
                    query += ' and version.status.name is "{}"'.format(asset_status)

                all_components = self.session.query(query
                ).all()

                if not all_components:
                    continue

                sorted_components = sorted(all_components, key=lambda k: int(k['version']['version']))

                final_component = sorted_components[-1]
                self._result_data[taskItem] = final_component['id']

        # Update window title with the amount of clips found matching the filters
        new_title = self._window_title + ' - ({} clips found)'.format(len(self._result_data))
        self.setWindowTitle(new_title)

        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDisabled(not bool(len(self._result_data)))
        self._tracknameField.setText(self.suggested_track_name)

    def populate_components(self):
        ''' Populate the components widget. '''
        all_component_names = []

        context_leafs = self._get_context_leafs(self.parsed_selection.values())

        for context in context_leafs:
            task_query = 'select name from Component where version.asset.parent.id is "{}"'.format(context['id'])
            components = self.session.query(task_query).all()

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
        ''' Populate the asset status widget. '''
        statuses = self.session.query('Status').all()
        self.asset_status_combobox.addItem('- ANY -')
        for status in statuses:
            self.asset_status_combobox.addItem(status['name'])

    def populate_asset_types(self):
        ''' Populate the asset types widget. '''
        all_asset_types_names = []
        context_leafs = self._get_context_leafs(self.parsed_selection.values())

        for context in context_leafs:
            task_query = 'select type, type.name, name from Asset where parent.id is "{}"'.format(context['id'])
            assets = self.session.query(task_query).all()

            if not assets:
                continue

            all_asset_types_names.append([asset['type']['name'] for asset in assets])
        common_asset_types = self.common_items(all_asset_types_names)
        for name in sorted(common_asset_types):
            self.asset_type_combobox.addItem(name)

    def populate_tasks(self):
        ''' Populate the tasks widget. '''
        all_tasks=[]
        context_leafs = self._get_context_leafs(self.parsed_selection.values())

        for context in context_leafs:
            task_query = 'select name from Task where parent.id is "{}"'.format(context['id'])
            tasks = self.session.query(task_query).all()

            if not tasks:
                continue

            all_tasks.append([task['name'] for task in tasks])

        common_tasks = self.common_items(all_tasks)
        for name in sorted(common_tasks):
            self.tasks_combobox.addItem(name)


class FtrackReBuildServerTrackAction(BuildTrackActionBase, FtrackBase):
    '''Rebuild from server action.'''

    def __init__(self):
        ''' Initialise action. '''
        super(FtrackReBuildServerTrackAction, self).__init__('Build track from ftrack')
        self.trackFinder = FtrackTrackFinderByNameWithDialog(self)
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoLight'))

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def getExternalFilePaths(self, trackItem):
        ''''Return the files path for the given *trackItem*. '''
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
        ''''Return the expected frame range for the given *trackItem*. '''
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
        ''''Return current trackName. '''
        return self._trackName

    def configure(self, project, selection):
        ''''Return whether the widget is configured correctly given *project* and *selection*. '''
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
        '''' Execute action. '''
        selection = self.getTrackItems()

        sequence = hiero.ui.activeView().sequence()
        project = sequence.project()


        if not self.configure(project, selection):
          return

        self._buildTrack(selection, sequence, project)

        if self._errors:
          msgBox = QtWidgets.QMessageBox(hiero.ui.mainWindow())
          msgBox.setWindowTitle('Build track from ftrack')
          msgBox.setText('There were problems building the track.')
          msgBox.setDetailedText( '\n'.join(self._errors) )
          msgBox.exec_()
          self._errors = []

    @staticmethod
    def update_ftrack_versions(track_item):
        '''' Force update *trackIten* to fetch all available versions'''
        track_item.source().rescan()  # First rescan the current clip
        if track_item.isMediaPresent():
            version = track_item.currentVersion()
            scanner = hiero.core.VersionScanner.VersionScanner()  # Scan for new versions
            scanner.doScan(version)

    def _buildTrackItem(self, name, clip, originalTrackItem, expected_start_time, expectedDuration, expected_start_handle,
                        expectedEndHandle, expectedOffset):
        '''' Return a trackItem build out of:

        *name*, *clip*, *originalTrackItem*, *expectedStartTime*, *expectedDuration*, *expectedStartHandle*,
        *expectedEndHandle*, *expectedOffset*.

        '''
        # Create the item
        track_item = hiero.core.TrackItem(name, hiero.core.TrackItem.kVideo)
        track_item.setSource(clip)

        # Copy the timeline in/out
        track_item.setTimelineIn(originalTrackItem.timelineIn())
        track_item.setTimelineOut(originalTrackItem.timelineOut())

        # Calculate the source in/out times.  Try to match frame numbers, compensating for handles etc.
        media_source = clip.mediaSource()

        original_clip = originalTrackItem.source()
        original_media_source = original_clip.mediaSource()

        # If source durations match, and there were no retimes, then the whole clip was exported, and we should use the same source in/out
        # as the original.  The correct handles are not being stored in the tag in this case.
        full_clip_exported = (original_media_source.duration() == media_source.duration())

        if full_clip_exported:
            source_in = originalTrackItem.sourceIn()
            source_out = originalTrackItem.sourceOut()

        # Otherwise try to use the export handles and retime info to determine the correct source in/out
        else:
            # On the timeline, the first frame of video files is always 0.  Reset the start time
            is_video_file = hiero.core.isVideoFileExtension(os.path.splitext(media_source.fileinfos()[0].filename())[1])
            if is_video_file:
                expected_start_time = 0

            source_in = expected_start_time - media_source.startTime()
            if expected_start_handle is not None:
                source_in += expected_start_handle

            # First add the abs src duration to get the source out
            source_out = source_in + abs(originalTrackItem.sourceOut() - originalTrackItem.sourceIn())

            # Then, for a negative retime, src in/out need to be reversed
            if originalTrackItem.playbackSpeed() < 0.0:
                source_in, source_out = source_out, source_in

        track_item.setSourceIn(source_in)
        track_item.setSourceOut(source_out)

        component_id = self._track_data.get(originalTrackItem)
        if component_id:
            component = self.session.get('Component', component_id)
            add_ftrack_build_tag(clip, component)
            self.update_ftrack_versions(track_item)

        return track_item


class FtrackBuildTrack(BuildTrack):
    '''Build track menu.'''

    def __init__(self):
        ''' Initialise menu widget. '''
        QtWidgets.QMenu.__init__(self, 'Build track from ftrack', None)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        hiero.core.events.registerInterest('kShowContextMenu/kTimeline', self.eventHandler)
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoLight'))
        self._action_rebuild_from_server = FtrackReBuildServerTrackAction()
        self.addAction(self._action_rebuild_from_server)

    def eventHandler(self, event):
        ''' Check whether the menu can be enabled given the *event*. '''
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
