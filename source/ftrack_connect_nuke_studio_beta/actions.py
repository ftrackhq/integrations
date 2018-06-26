from QtExt import QtWidgets, QtGui, QtCore

from ftrack_connect_nuke_studio_beta.base import FtrackBase

from hiero.ui.BuildExternalMediaTrack import BuildTrackFromExportTagAction, BuildTrack


class FtrackBuildTrackFromExportTagAction(BuildTrackFromExportTagAction, FtrackBase):

    def __init__(self):
        BuildTrackFromExportTagAction.__init__(self)
        FtrackBase.__init__(self)
        # self.setTitle('Build Track From ftrack Tag')


class FtrackBuildTrack(BuildTrack):
    def __init__(self):
        super(FtrackBuildTrack, self).__init__()
        self.setTitle('[ftrack] Build Track')
        self.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoColor'))
        self._actionTag = FtrackBuildTrackFromExportTagAction()
