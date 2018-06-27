import logging

from QtExt import QtWidgets, QtGui, QtCore


from ftrack_connect_nuke_studio_beta.base import FtrackBase

import hiero
from hiero.ui.BuildExternalMediaTrack import BuildTrackFromExportTagAction, BuildExternalMediaTrackAction, BuildTrack


class FtrackBuildTrackFromExportTagAction(BuildTrackFromExportTagAction, FtrackBase):

    def __init__(self):
        BuildTrackFromExportTagAction.__init__(self)
        FtrackBase.__init__(self)
        self.setText("ftrack :: Build Track From Tag")

    def trackItemAdded(self, newTrackItem, track, originalTrackItem):
        self.logger.info('trackItemAdded')
        """ Reimplementation.  Adds a tag to the new track item, and copies any retime effects if necessary. """
        # Find export tag on the original track item
        tag = self.findTag(originalTrackItem)
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
            if metadata.hasKey("tag.presetid"):
                newTag = hiero.core.Tag("Ftrack", ':ftrack/image/default/ftrackLogoColor', False)
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


class FtrackBuildTrack(BuildTrack, FtrackBase):
    def __init__(self):
        QtWidgets.QMenu.__init__(self, "ftrack :: Build Track", None)

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
                else:
                    self.logger.info('skipping:{0}'.format(tag_metadata))

        self.logger.info('enable action tag: {0}'.format(bool(len(ftrack_tags))))
        self._actionTag.setEnabled(len(ftrack_tags) > 0)
        self.logger.info(self._actionTag.isEnabled())
