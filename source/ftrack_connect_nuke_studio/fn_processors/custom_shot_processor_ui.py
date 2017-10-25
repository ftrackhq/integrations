import hiero.core
import hiero.ui
from PySide import QtCore, QtGui

from hiero.exporters import FnShotProcessorUI, FnShotProcessor
from hiero.exporters import FnTranscodeExporterUI, FnTranscodeExporter

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog


class FtrackShotProcessorUI(hiero.ui.ProcessorUIBase, QtCore.QObject):

    def __init__(self, preset):
        QtCore.QObject.__init__(self)
        hiero.ui.ProcessorUIBase.__init__(
            self,
            preset,
            itemTypes=hiero.core.TaskPresetBase.kTrackItem
        )

        self.processors = {
            'Plate': FnTranscodeExporterUI.TranscodeExporterUI(
                FnTranscodeExporter.TranscodePreset('Plate', {})
            )
        }

    def createProcessorSettingsWidget(self, exportItems):
        for name, fn in self.processors.items():
            widget = QtGui.QWidget()
            fn.populateUI(widget, None)
            self._tabWidget.addTab(widget, name)

    def populateUI(self, widget, exportItems, editMode):
        self._taskUILayout = QtGui.QVBoxLayout(widget)
        self._taskUILayout.setContentsMargins(10, 0, 0, 0)
        self._tabWidget = QtGui.QTabWidget()
        self._taskUILayout.addWidget(self._tabWidget)

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

        self.createProcessorSettingsWidget(exportItems)

        projectTreeDialog.export_project_button.hide()
        projectTreeDialog.close_button.hide()

    def displayName(self):
        return "[ftrack] Process as Shots"

    def toolTip(self):
        return "Process as Shots generates output on a per shot basis."
