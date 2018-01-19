import hiero.core
import hiero.ui
from QtExt import QtCore, QtWidgets
from hiero.ui.FnTagFilterWidget import TagFilterWidget

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI

class FtrackShotProcessorUI(ShotProcessorUI, FtrackBase):

    def __init__(self, preset):
        FtrackBase.__init__(self)
        ShotProcessorUI.__init__(
            self,
            preset,
        )

    def displayName(self):
        return "Ftrack"

    def toolTip(self):
        return "Process as Shots generates output on a per shot basis."
            
    def _checkExistingVersions(self, exportItems):
        """ Iterate over all the track items which are set to be exported, and check if they have previously
        been exported with the same version as the setting in the current preset.  If yes, show a message box
        asking the user if they would like to increment the version, or overwrite it. """

        for item in exportItems:
            self.logger.info('_checkExistingVersions of:{0}'.format(item.name()))

        return ShotProcessorUI._checkExistingVersions(
            self,
            exportItems,
        )

    def onItemSelected(self, item):
        self.logger.info(item.track)
    
    # def createPathPreviewWidget(self):
    #     # here we can manipulate the path preview
