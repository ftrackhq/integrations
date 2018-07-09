import logging
import collections
from QtExt import QtWidgets, QtGui, QtCore


from ftrack_connect_nuke_studio_beta.base import FtrackBase

import hiero
from hiero.ui.BuildExternalMediaTrack import (
    BuildTrack,
    BuildTrackFromExportTagAction,
    BuildTrackFromExportTagDialog,
    BuildExternalMediaTrackAction,
    BuildExternalMediaTrackDialog,
    TrackFinderByNameWithDialog
)


class FtracBuildServerTrackDialog(QtWidgets.QDialog, FtrackBase):
    task_changed = QtCore.Signal()

    @staticmethod
    def common_items(items):
        return set.intersection(*map(set, items))

    def itemProject(self, item):
        if hasattr(item, 'project'):
            return item.project()
        elif hasattr(item, 'parent'):
            return self.itemProject(item.parent())
        else:
            return None

    def __init__(self, selection, parent=None):
        if not parent:
            parent = hiero.ui.mainWindow()
        super(FtracBuildServerTrackDialog, self).__init__(parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

        self._selection = selection

        if self._selection:
            self.project = self.itemProject(self._selection[0])

        self.setWindowTitle("Build Track From server tasks")
        self.setSizeGripEnabled(True)

        layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        self._tracknameField = QtWidgets.QLineEdit(BuildTrack.ProjectTrackNameDefault(selection))
        self._tracknameField.setToolTip("Name of new track")

        self.tasks_combobox = QtWidgets.QComboBox()
        formLayout.addRow("Task:", self.tasks_combobox)

        self.asset_type_combobox = QtWidgets.QComboBox()
        formLayout.addRow("Asset Type:", self.asset_type_combobox)

        self.compomnent_combobox = QtWidgets.QComboBox()
        formLayout.addRow("Component :", self.compomnent_combobox)

        layout.addLayout(formLayout)
        self.setLayout(layout)

        # populate data
        self.populate_tasks()
        self.populate_asset_types()

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


# =========================================================================================
# Track creation dialog

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

# =========================================================================================
# External media dialog and action


class FtrackBuildExternalMediaTrackDialog(BuildExternalMediaTrackDialog):
    def __init__(self, selection, parent=None):

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

        if not parent:
            parent = hiero.ui.mainWindow()
        super(BuildExternalMediaTrackDialog, self).__init__(parent)
        self.setWindowTitle('Build Track From Export Structure')
        self.setSizeGripEnabled(True)

        self._exportTemplate = None
        self._selection = selection
        layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()

        self._tracknameField = QtWidgets.QLineEdit(BuildTrack.ProjectTrackNameDefault(selection))
        self._tracknameField.setToolTip('Name of new track')
        validator = hiero.ui.trackNameValidator()
        self._tracknameField.setValidator(validator)
        formLayout.addRow('Track Name:', self._tracknameField)

        project = None
        if self._selection:
            project = self.itemProject(self._selection[0])

        all_presets = hiero.core.taskRegistry.localPresets() + hiero.core.taskRegistry.projectPresets(project)
        filtered_presets = [preset for preset in all_presets if preset.properties().get('ftrack', {}).get('asset_name') is not None]

        presetNames = [preset.name() for preset in filtered_presets]

        presetCombo = QtWidgets.QComboBox()
        for name in sorted(presetNames):
            presetCombo.addItem(name)
        presetCombo.currentIndexChanged.connect(self.presetChanged)
        self._presetCombo = presetCombo
        formLayout.addRow('Export Preset:', presetCombo)

        layout.addLayout(formLayout)

        self._exportTemplate = hiero.core.ExportStructure2()
        self._exportTemplateViewer = hiero.ui.ExportStructureViewer(self._exportTemplate, hiero.ui.ExportStructureViewer.ReadOnly)
        if project:
            self._exportTemplateViewer.setProject(project)

        layout.addWidget(self._exportTemplateViewer)

        # Add the standard ok/cancel buttons, default to ok.
        self._buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText('Build')
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setDefault(True)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setToolTip('Builds the selected entry in the export template. Only enabled if an entry is selected in the view above.')
        self._buttonbox.accepted.connect(self.acceptTest)
        self._buttonbox.rejected.connect(self.reject)
        layout.addWidget(self._buttonbox)

        if presetNames:
            self.presetChanged(presetNames[0])

        self.setLayout(layout)


class FtrackBuildExternalMediaTrackAction(BuildExternalMediaTrackAction):

    def __init__(self):
        super(FtrackBuildExternalMediaTrackAction, self).__init__()
        self.setText('From ftrack structure')
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))
        self.trackFinder = FtrackTrackFinderByNameWithDialog(self)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

    def configure(self, project, selection):
        dialog = FtracBuildServerTrackDialog(selection)
        if dialog.exec_():
            self._trackName = dialog.trackName()

            # Determine the exported file paths
            self._exportTemplate = dialog._exportTemplate
            structureElement = dialog._exportTemplateViewer.selection()
            self._processorPreset = dialog._preset
            if structureElement is not None:
                # Grab the elements relative path
                self._elementPath = structureElement.path()
                self._elementPreset = structureElement.preset()

                # If task presets lacks of some information, let's rely on the processor ones.
                if not self._elementPreset.properties()['ftrack'].get('project_schema'):
                    processor_schema = self._processorPreset.properties()['ftrack']['project_schema']
                    self._elementPreset.properties()['ftrack']['project_schema'] = processor_schema

                if not self._elementPreset.properties()['ftrack'].get('task_type'):
                    task_type = self._processorPreset.properties()['ftrack']['task_type']
                    self._elementPreset.properties()['ftrack']['task_type'] = task_type

                if not self._elementPreset.properties()['ftrack'].get('asset_type_code'):
                    asset_type_code = self._processorPreset.properties()['ftrack']['asset_type_code']
                    self._elementPreset.properties()['ftrack']['asset_type_code'] = asset_type_code

                if not self._elementPreset.properties()['ftrack'].get('asset_name'):
                    asset_name = self._processorPreset.properties()['ftrack']['asset_name']
                    self._elementPreset.properties()['ftrack']['asset_name'] = asset_name

                resolver = hiero.core.ResolveTable()
                resolver.merge(dialog._resolver)
                resolver.merge(self._elementPreset.createResolver())
                self._resolver = resolver

                self._project = project

                return True

        return False


# =========================================================================================
# Tag dialog and action


class FtrackBuildTrackFromExportTagDialog(BuildTrackFromExportTagDialog):

    def __init__(self, selection, createCompClips, parent=None):
        if not parent:
            parent = hiero.ui.mainWindow()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

        super(BuildTrackFromExportTagDialog, self).__init__(parent)

        self.setWindowTitle('Build Track From ftrack Export Tag')
        self.setWindowIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))

        self.setSizeGripEnabled(True)

        self._tagIdentifier = None

        layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        formLayout.setRowWrapPolicy(QtWidgets.QFormLayout.WrapAllRows)
        self._tracknameField = QtWidgets.QLineEdit(BuildTrack.ProjectTrackNameDefault(selection))
        self._tracknameField.setToolTip('Name of new track')
        validator = hiero.ui.trackNameValidator()
        self._tracknameField.setValidator(validator)

        formLayout.addRow('Track Name:', self._tracknameField)

        # Use an OrderedDict so the tags are displayed in creation order
        self._tagData = collections.OrderedDict()

        for item in selection:
            if hasattr(item, 'tags'):
                for tag in item.tags():
                    tagMetadata = tag.metadata()

                    if tagMetadata.hasKey('path') and tagMetadata.hasKey('provider'):
                        if not tagMetadata.value('provider') == 'ftrack':
                            continue
                        identifier = BuildTrack.GetTagIdentifier(tag)
                        data = self._tagData.get(identifier, dict())
                        if not data:
                            data['icon'] = tag.icon()
                            data['tagname'] = tag.name()
                            if tagMetadata.hasKey('description'):
                                data['description'] = tagMetadata.value('description')
                            if tagMetadata.hasKey('pathtemplate'):
                                data['pathtemplate'] = tagMetadata.value('pathtemplate')
                            data['itemnames'] = []
                            self._tagData[identifier] = data
                        data['itemnames'].append(item.name())

        self._notesView = QtWidgets.QTextEdit()
        self._notesView.setReadOnly(True)

        # List box for track selection
        self._tagListModel = QtGui.QStandardItemModel()
        self._tagListView = QtWidgets.QListView()
        self._tagListView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self._tagListView.setModel(self._tagListModel)
        for tagIdentifier, tagData in self._tagData.iteritems():
            item = QtGui.QStandardItem(tagData['tagname'])
            item.setData(tagIdentifier)
            item.setEditable(False)
            itemlist = tagData['itemnames']
            item.setToolTip('%i Items with this tag: \n%s' % (len(itemlist), '\n'.join(itemlist)))
            item.setIcon(QtGui.QIcon(tagData['icon']))
            self._tagListModel.appendRow(item)

        tagListSelectionModel = self._tagListView.selectionModel()
        tagListSelectionModel.selectionChanged.connect(self.tagSelectionChanged)

        # Start with the last tag selected
        tagListSelectionModel.select(self._tagListModel.index(self._tagListModel.rowCount() - 1, 0),
                                     QtCore.QItemSelectionModel.Select)

        tagLayout = QtWidgets.QHBoxLayout()
        tagLayout.addWidget(self._tagListView)
        tagLayout.addWidget(self._notesView)

        formLayout.addRow('Select Export Tag:', tagLayout)

        createCompClipsCheckBox = QtWidgets.QCheckBox('Create Comp Clips')
        createCompClipsCheckBox.setVisible(False)  # Disable for now

        createCompClipsCheckBox.setToolTip(
            'When building from a Nuke Project export, this controls whether the created clips reference the exported nk script or the render output.')
        createCompClipsCheckBox.setChecked(createCompClips)
        formLayout.addRow(createCompClipsCheckBox)
        self._createCompClipsCheckBox = createCompClipsCheckBox

        layout.addLayout(formLayout)

        # Add the standard ok/cancel buttons, default to ok.
        self._buttonbox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText('Build')
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setAutoDefault(True)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setToolTip(
            'Resolves the exported item from the selected export tags.')
        self._buttonbox.accepted.connect(self.acceptTest)
        self._buttonbox.rejected.connect(self.reject)
        layout.addWidget(self._buttonbox)

        self.setLayout(layout)


class FtrackBuildTrackFromExportTagAction(BuildTrackFromExportTagAction, FtrackBase):

    def __init__(self):
        BuildTrackFromExportTagAction.__init__(self)
        FtrackBase.__init__(self)
        self.setText('From ftrack Tag')
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))
        self.trackFinder = FtrackTrackFinderByNameWithDialog(self)

    def configure(self, project, selection):

        # Check the preferences for whether the built clips should be comp clips in the
        # case that the export being built from was a Nuke Shot export.
        settings = hiero.core.ApplicationSettings()
        # createCompClips = settings.boolValue(self.kCreateCompClipsPreferenceKey, False)
        createCompClips = False

        dialog = FtrackBuildTrackFromExportTagDialog(selection, createCompClips)
        if dialog.exec_():
            self._trackName = dialog.trackName()
            self._tagIdentifier = dialog.tagIdentifier()
            self._createCompClips = dialog.createCompClips()

            # Write the create comp clips choice to the preferences
            settings.setBoolValue(self.kCreateCompClipsPreferenceKey, self._createCompClips)

            return True
        else:
            return False


# =========================================================================================
# Main Menu

class FtrackBuildTrack(BuildTrack, FtrackBase):

    def __init__(self):
        QtWidgets.QMenu.__init__(self, 'Build Track', None)

        hiero.core.events.registerInterest('kShowContextMenu/kTimeline', self.eventHandler)
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))
        self._actionStructure = FtrackBuildExternalMediaTrackAction()
        self._actionTag = FtrackBuildTrackFromExportTagAction()

        self.addAction(self._actionTag)
        self.addAction(self._actionStructure)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

    def eventHandler(self, event):
        super(FtrackBuildTrack, self).eventHandler(event)
        selection = event.sender.selection()

        ftrack_tags = []
        for item in selection:
            if not hasattr(item, 'tags'):
                continue

            for tag in item.tags():
                tag_metadata = tag.metadata()
                # filter ftrack tags only
                if tag_metadata.hasKey('provider') and tag_metadata.value('provider') == 'ftrack':
                    ftrack_tags.append(tag)

        self._actionTag.setEnabled(len(ftrack_tags) > 0)

    def findShotExporterTag(self, trackItem):
        ''' Try to find a tag added by the Nuke Shot Exporter by checking it has the expected metadata keys. '''
        return self._findTagWithMetadataKeys(trackItem, ('tag.provider', 'tag.presetid', 'tag.path', 'tag.script'))
