import hiero.core
import hiero.ui
from QtExt import QtGui, QtCore, QtWidgets

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
import logging


class FtrackShotProcessorUI(hiero.ui.ProcessorUIBase, QtCore.QObject):

    def __init__(self, preset):
        QtCore.QObject.__init__(self)
        hiero.ui.ProcessorUIBase.__init__(
            self,
            preset,
            itemTypes=hiero.core.TaskPresetBase.kTrackItem
        )
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

        self.widgets = []
        self.projectTreeDialog = None

    def processors(self):
        return self.preset().properties()['processors']

    def createProcessorSettingsWidget(self, exportItems):
        processors = self.processors()
        for name, preset in processors:
            proc_ui = hiero.ui.taskUIRegistry.getTaskUIForPreset(preset)
            widget = QtWidgets.QWidget()
            self.widgets.append(widget)
            template = hiero.core.ExportStructure2()
            proc_ui.populateUI(widget, template)
            self._tabWidget.addTab(widget, name)

    def populateUI(self, processorUIWidget, taskUIWidget, exportItems):
        self._taskUILayout = QtWidgets.QVBoxLayout(processorUIWidget)
        self._taskUILayout.setContentsMargins(10, 0, 0, 0)
        self._tabWidget = QtWidgets.QTabWidget()
        self._taskUILayout.addWidget(self._tabWidget)

        ftags = []
        sequence = None
        for item in exportItems:
            hiero_item = item.item()
            if not isinstance(hiero_item, hiero.core.TrackItem):
                continue

            # update_tag_value_from_name(item)

            tags = hiero_item.tags()
            tags = [tag for tag in tags if tag.metadata().hasKey(
                'ftrack.type'
            )]
            ftags.append((hiero_item, tags))
            sequence = hiero_item.sequence()

        self.projectTreeDialog = ProjectTreeDialog(
            data=ftags, parent=processorUIWidget, sequence=sequence
        )

        self._tabWidget.insertTab(0, self.projectTreeDialog, 'ftrack')

        self.createProcessorSettingsWidget(exportItems)

        self.projectTreeDialog.export_project_button.hide()
        self.projectTreeDialog.close_button.hide()

    def displayName(self):
        return "[ftrack] Project Exporter"

    def toolTip(self):
        return "Process as Shots generates output on a per shot basis."
