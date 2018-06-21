from QtExt import QtWidgets

import hiero
from ftrack_connect_nuke_studio_beta.base import FtrackBase


class FtrackVersionHandler(QtWidgets.QAction, FtrackBase):

    def __init__(self):
        super(FtrackVersionHandler, self).__init__("[ftrack] change versions", None)
        self.triggered.connect(self.doit)

        hiero.core.events.registerInterest(
            (hiero.core.events.EventType.kShowContextMenu, hiero.core.events.EventType.kTimeline),
            self.eventHandler
        )

    def doit(self):
        #doing something....
        return

    def _menuActionsAreEnabled(self, versionMenu):
        """Check if actions in versionMenu are enabled to add this action"""
        versionActions = versionMenu.actions()
        enabledActions = [action for action in versionActions if action.isEnabled()]
        return len(enabledActions) > 0

    def eventHandler(self, event):
        enabled = False
        if hasattr(event.sender, 'selection'):
            s = event.sender.selection()
            if len(s) >= 1:
                enabled = True

            # enable/disable the action each time
            if enabled:
                for a in event.menu.actions():
                    if a.text().lower().strip() == "version":
                        if self._menuActionsAreEnabled(a.menu()):
                            hiero.ui.insertMenuAction(
                                self, a.menu(),
                                before="foundry.project.versionup"
                            )
                            break

      # Get all selected active versions
    def selectedVersions(self):
        selection = hiero.ui.currentContextMenuView().selection()
        versions = []
        self.findActiveVersions(selection, versions)
        return (versions)


version_action = FtrackVersionHandler()
