import hiero.core
import hiero.ui
from QtExt import QtCore, QtWidgets
from hiero.ui.FnTagFilterWidget import TagFilterWidget

from ftrack_connect_nuke_studio.ui.create_project import ProjectTreeDialog
from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessorUI import ShotProcessorUI
from ftrack_export_structure import FtrackExportStructureViewer

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
    

    def populateUI(self, *args, **kwargs):

        """ Build the processor UI and add it to widget. """
        if self.hiero_version_touple >= (10, 5, 1):
            (processorUIWidget, taskUIWidget, exportItems) = args
        else:
            (processorUIWidget, exportItems, editMode) = args

        self._exportItems = exportItems

        self._tags = self.findTagsForItems(exportItems)

        layout = QtWidgets.QVBoxLayout(processorUIWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.setChildrenCollapsible(False);
        splitter.setHandleWidth(10);
        layout.addWidget(splitter)
        
        self._editMode = hiero.ui.IProcessorUI.ReadOnly if self._preset.readOnly() else hiero.ui.IProcessorUI.Full

        # The same enums are declared in 2 classes.  They should have the same values but to be sure, map between them
        editModeMap = { hiero.ui.IProcessorUI.ReadOnly : FtrackExportStructureViewer.ReadOnly,
                        hiero.ui.IProcessorUI.Limited : FtrackExportStructureViewer.Limited,
                        hiero.ui.IProcessorUI.Full : FtrackExportStructureViewer.Full }

        structureViewerMode = editModeMap[self._editMode]
        
        ###EXPORT STRUCTURE
        exportStructureWidget = QtWidgets.QWidget()
        splitter.addWidget(exportStructureWidget)
        exportStructureLayout =  QtWidgets.QVBoxLayout(exportStructureWidget)
        exportStructureLayout.setContentsMargins(0, 0, 0, 9)
        self._exportStructureViewer = FtrackExportStructureViewer(self._exportTemplate, structureViewerMode)
        exportStructureLayout.addWidget(self._exportStructureViewer)
        self._project = self.projectFromSelection(exportItems)
        if self._project:
            self._exportStructureViewer.setProject(self._project)

        self._exportStructureViewer.destroyed.connect(self.onExportStructureViewerDestroyed)

        self._exportStructureViewer.setItemTypes(self._itemTypes)
        self._preset.createResolver().addEntriesToExportStructureViewer(self._exportStructureViewer)
        self._exportStructureViewer.structureModified.connect(self.onExportStructureModified)
        self._exportStructureViewer.selectionChanged.connect(self.onExportStructureSelectionChanged)

        exportStructureLayout.addWidget(self.createVersionWidget())

        exportStructureLayout.addWidget(self.createPathPreviewWidget())

        splitter.addWidget(self.createProcessorSettingsWidget(exportItems))

        taskUILayout = QtWidgets.QVBoxLayout(taskUIWidget)
        taskUILayout.setContentsMargins(10, 0, 0, 0)
        tabWidget = QtWidgets.QTabWidget()
        taskUILayout.addWidget(tabWidget)
        self._contentScrollArea = QtWidgets.QScrollArea()
        tabWidget.addTab(self._contentScrollArea, "Content")
        self._contentScrollArea.setFrameStyle( QtWidgets.QScrollArea.NoFrame )
        self._contentScrollArea.setWidgetResizable(True)



