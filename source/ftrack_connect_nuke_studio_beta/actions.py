import logging
import collections
from QtExt import QtWidgets, QtGui, QtCore


from ftrack_connect_nuke_studio_beta.base import FtrackBase

import hiero
from hiero.ui.BuildExternalMediaTrack import BuildTrackFromExportTagAction, BuildExternalMediaTrackAction, BuildTrack, BuildTrackFromExportTagDialog


class FtrackBuildTrackFromExportTagDialog(BuildTrackFromExportTagDialog):

    def __init__(self, selection, createCompClips, parent=None):
        if not parent:
            parent = hiero.ui.mainWindow()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

        super(BuildTrackFromExportTagDialog, self).__init__(parent)

        self.setWindowTitle("Build Track From ftrack Export Tag")
        self.setWindowIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))

        self.setSizeGripEnabled(True)

        self._tagIdentifier = None

        layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        formLayout.setRowWrapPolicy(QtWidgets.QFormLayout.WrapAllRows)
        self._tracknameField = QtWidgets.QLineEdit(BuildTrack.ProjectTrackNameDefault(selection))
        self._tracknameField.setToolTip("Name of new track")
        validator = hiero.ui.trackNameValidator()
        self._tracknameField.setValidator(validator)

        formLayout.addRow("Track Name:", self._tracknameField)

        # Use an OrderedDict so the tags are displayed in creation order
        self._tagData = collections.OrderedDict()

        for item in selection:
            if hasattr(item, 'tags'):
                for tag in item.tags():
                    tagMetadata = tag.metadata()
                    self.logger.info(tagMetadata)

                    if tagMetadata.hasKey("path") and tagMetadata.hasKey("provider"):
                        if not tagMetadata.value('provider') == 'ftrack':
                            continue
                        identifier = BuildTrack.GetTagIdentifier(tag)
                        data = self._tagData.get(identifier, dict())
                        if not data:
                            data["icon"] = tag.icon()
                            data["tagname"] = tag.name()
                            if tagMetadata.hasKey("description"):
                                data["description"] = tagMetadata.value("description")
                            if tagMetadata.hasKey("pathtemplate"):
                                data["pathtemplate"] = tagMetadata.value("pathtemplate")
                            data["itemnames"] = []
                            self._tagData[identifier] = data
                        data["itemnames"].append(item.name())

        self._notesView = QtWidgets.QTextEdit()
        self._notesView.setReadOnly(True)

        # List box for track selection
        self._tagListModel = QtGui.QStandardItemModel()
        self._tagListView = QtWidgets.QListView()
        self._tagListView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self._tagListView.setModel(self._tagListModel)
        for tagIdentifier, tagData in self._tagData.iteritems():
            item = QtGui.QStandardItem(tagData["tagname"])
            item.setData(tagIdentifier)
            item.setEditable(False)
            itemlist = tagData["itemnames"]
            item.setToolTip("%i Items with this tag: \n%s" % (len(itemlist), "\n".join(itemlist)))
            item.setIcon(QtGui.QIcon(tagData["icon"]))
            self._tagListModel.appendRow(item)

        tagListSelectionModel = self._tagListView.selectionModel()
        tagListSelectionModel.selectionChanged.connect(self.tagSelectionChanged)

        # Start with the last tag selected
        tagListSelectionModel.select(self._tagListModel.index(self._tagListModel.rowCount() - 1, 0),
                                     QtCore.QItemSelectionModel.Select)

        tagLayout = QtWidgets.QHBoxLayout()
        tagLayout.addWidget(self._tagListView)
        tagLayout.addWidget(self._notesView)

        formLayout.addRow("Select Export Tag:", tagLayout)

        createCompClipsCheckBox = QtWidgets.QCheckBox("Create Comp Clips")
        createCompClipsCheckBox.setVisible(False)  # Disable for now

        createCompClipsCheckBox.setToolTip(
            "When building from a Nuke Project export, this controls whether the created clips reference the exported nk script or the render output.")
        createCompClipsCheckBox.setChecked(createCompClips)
        formLayout.addRow(createCompClipsCheckBox)
        self._createCompClipsCheckBox = createCompClipsCheckBox

        layout.addLayout(formLayout)

        # Add the standard ok/cancel buttons, default to ok.
        self._buttonbox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Build")
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setAutoDefault(True)
        self._buttonbox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setToolTip(
            "Resolves the exported item from the selected export tags.")
        self._buttonbox.accepted.connect(self.acceptTest)
        self._buttonbox.rejected.connect(self.reject)
        layout.addWidget(self._buttonbox)

        self.setLayout(layout)


class FtrackBuildTrackFromExportTagAction(BuildTrackFromExportTagAction, FtrackBase):

    def __init__(self):
        BuildTrackFromExportTagAction.__init__(self)
        FtrackBase.__init__(self)
        self.setText("From ftrack Tag")
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))


    def trackItemAdded(self, newTrackItem, track, originalTrackItem):
        """ Reimplementation.  Adds a tag to the new track item, and copies any retime effects if necessary. """
        # Find export tag on the original track item
        tag = self.findTag(originalTrackItem)
        self.logger.info('trackItemAdded:: tag found {0}'.format(tag))

        if tag:
            # Add metadata referencing the newly created copied track item
            metadata = tag.metadata()

            # call setMetadataValue so that we only trigger something that's
            # undo/redo able if we need to
            self._setMetadataValue(metadata, "tag.track", track.guid())
            self._setMetadataValue(metadata, "tag.trackItem", newTrackItem.guid())

            # Tag the new track item to give it an icon.  Add a reference to the original
            # in the tag metadata.  This is used for re-export, so only add it if the original tag
            # has a presetid which could be re-exported from.
            self.logger.info('has presetid: {0}'.format(metadata.hasKey("tag.presetid")))

            if metadata.hasKey("tag.presetid"):
                newTag = hiero.core.Tag("ftrack", ':ftrack/image/default/ftrackLogoColor', False)
                newTag.metadata().setValue("tag.originaltrackitem", originalTrackItem.guid())
                newTag.setVisible( False )
                newTrackItem.addTag(newTag)

            # If retimes were not applied as part of the export, check for linked effects on the original track item, and
            # copy them to the new track.
            if not self.retimesAppliedInExport(tag):
                linkedRetimeEffects = [ item for item in originalTrackItem.linkedItems() if isinstance(item, hiero.core.EffectTrackItem) and item.isRetimeEffect() ]
                for effect in linkedRetimeEffects:
                    effectCopy = track.createEffect(copyFrom=effect, trackItem=newTrackItem)
                    effectCopy.setEnabled(effect.isEnabled())


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



class FtrackBuildTrack(BuildTrack, FtrackBase):
    def __init__(self):
        QtWidgets.QMenu.__init__(self, "Build Track", None)

        hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.eventHandler)
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))
        self._actionStructure = BuildExternalMediaTrackAction()
        self._actionTag = FtrackBuildTrackFromExportTagAction()

        self._actionStructure.setVisible(False)

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
        self.logger.info(self._actionTag.isEnabled())

    def findShotExporterTag(self, trackItem):
        """ Try to find a tag added by the Nuke Shot Exporter by checking it has the expected metadata keys. """
        return self._findTagWithMetadataKeys(trackItem, ("tag.provider", "tag.presetid", "tag.path", "tag.script"))
