import hiero.core
import hiero.ui

from hiero.exporters import FnShotProcessorUI

from custom_shot_processor import FtrackProcessorPreset

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
# from ftrack_connect_nuke_studio.ui.tag_manager import (
#     update_tag_value_from_name
# )


class FtrackShotProcessorUI(FnShotProcessorUI.ShotProcessorUI):

    def populateUI(self, widget, exportItems, editMode):
        FnShotProcessorUI.ShotProcessorUI.populateUI(
            self, widget, exportItems, editMode
        )

        # Hide export path UI
        self._exportStructureViewer.hide()

        ftags = []
        view = hiero.ui.activeView()
        track_items = view.selection()

        sequence = None
        for item in track_items:
            if not isinstance(item, hiero.core.TrackItem):
                continue

            # update_tag_value_from_name(item)

            tags = item.tags()
            tags = [tag for tag in tags if tag.metadata().hasKey(
                'ftrack.type'
            )]
            ftags.append((item, tags))
            sequence = item.sequence()

        projectTreeDialog = ProjectTreeDialog(
            data=ftags, parent=widget, sequence=sequence
        )

        self._tabWidget.insertTab(0, projectTreeDialog, 'ftrack')

        projectTreeDialog.export_project_button.hide()
        projectTreeDialog.close_button.hide()

    def displayName(self):
        return "[ftrack] Process as Shots"

    def toolTip(self):
        return "Process as Shots generates output on a per shot basis."
