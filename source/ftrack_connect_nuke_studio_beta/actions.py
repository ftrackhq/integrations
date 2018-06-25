from QtExt import QtWidgets

import hiero
from ftrack_connect_nuke_studio_beta.base import FtrackBase

from hiero.ui.BuildExternalMediaTrack import BuildTrackFromExportTagAction


class FtrackBuildTrackFromExportTagAction(BuildTrackFromExportTagAction, FtrackBase):

    def __init__(self):
        BuildTrackFromExportTagAction.__init__(self)
        FtrackBase.__init__(self)


version_action = FtrackBuildTrackFromExportTagAction()
