import hiero.core
import hiero.ui
from QtExt import QtCore, QtWidgets

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

        self.projectTreeDialog = None
        self._contentUI = {}
        
    def displayName(self):
        return "[ftrack] Project Exporter"

    def toolTip(self):
        return "Process as Shots generates output on a per shot basis."

    def createProcessorSettingsWidget(self, exportItems):
        self.logger.info('building processor widget')
        for path, preset in self._preset.properties()['exportTemplate']:
            task_ui = hiero.ui.taskUIRegistry.getNewTaskUIForPreset(preset)
            if task_ui:
                task_ui.setProject(self._project)
                task_ui.setTags(self._tags)
                taskUIWidget = QtWidgets.QWidget()
                self._contentUI[taskUIWidget] = task_ui
                task_ui.setTaskItemType(self.getTaskItemType())
                task_ui.initializeAndPopulateUI(taskUIWidget, self._exportTemplate)
                self._tabWidget.addTab(taskUIWidget, preset.name())
                try:
                    taskUI.propertiesChanged.connect(self.onExportStructureModified,
                                                type=QtCore.Qt.UniqueConnection)
                except:
                    # Signal already connected.
                    pass

    def _checkExistingVersions(self, exportItems):
        """ Iterate over all the track items which are set to be exported, and check if they have previously
        been exported with the same version as the setting in the current preset.  If yes, show a message box
        asking the user if they would like to increment the version, or overwrite it. """
        self.logger.info('_checkExistingVersions')
        return ShotProcessorUI._checkExistingVersions(
            self,
            exportItems,
        )

    def setTaskContent(self, preset):
        """ Get the UI for a task preset and add it in the 'Content' tab. """
        # First clear the old task UI.  It's important that this doesn't live longer
        # than the widgets it created, otherwise it can lead to crashes in PySide2.
        self.logger.info('setTaskContent with: {0}'.format(preset))
        return ShotProcessorUI.setTaskContent(
            self,
            preset,
        )

    def refreshContent(self):
        self.logger.info('refreshContent')
        return ShotProcessorUI.refreshContent(
            self,
        )        

    def createHandleWidgets(self):
        self.logger.info('createHandleWidgets with')
        return ShotProcessorUI.createHandleWidgets(self)


    def populateUI(self, *args, **kwargs):
        if self.hiero_version_touple >= (10, 5, 1):
            (widget, taskUIWidget, exportItems) = args
        else:
            (widget, exportItems, editMode) = args

        self._taskUILayout = QtWidgets.QVBoxLayout(widget)
        self._taskUILayout.setContentsMargins(10, 0, 0, 0)
        self._tabWidget = QtWidgets.QTabWidget()
        self._taskUILayout.addWidget(self._tabWidget)
        self._tags = self.findTagsForItems(exportItems)
        self._editMode = hiero.ui.IProcessorUI.ReadOnly if self._preset.readOnly() else hiero.ui.IProcessorUI.Full

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
            data=ftags, parent=widget, sequence=sequence
        )

        self._tabWidget.insertTab(0, self.projectTreeDialog, 'ftrack')

        self.createProcessorSettingsWidget(exportItems)

        self.projectTreeDialog.export_project_button.hide()
        self.projectTreeDialog.close_button.hide()
