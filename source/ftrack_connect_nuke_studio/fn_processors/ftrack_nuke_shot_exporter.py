import hiero.core
import hiero.core.util
import hiero.core.nuke as nuke
import _nuke # import _nuke so it does not conflict with hiero.core.nuke

from hiero.exporters.FnNukeShotExporter import NukeShotExporter, NukeShotPreset
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI

from hiero.ui.FnUIProperty import UIPropertyFactory

from hiero.exporters import FnShotExporter
from hiero.exporters import FnExternalRender
from hiero.exporters import FnScriptLayout

from QtExt import QtWidgets, QtGui, QtCore

from ftrack_base import FtrackBase


class FtrackNukeShotExporter(NukeShotExporter, FtrackBase):
    def __init__(self, initDict):
        super(FtrackNukeShotExporter, self).__init__(initDict)

    def taskStep(self):
        self.logger.info('TaskStep...')
        super(FtrackNukeShotExporter, self).taskStep()

    def startTask(self):
        self.logger.info('Starting Task')
        return super(FtrackNukeShotExporter, self).startTask()
    
    def finishTask(self):
        self.logger.info('Finishing Task')
        super(FtrackNukeShotExporter, self).finishTask()


class FtrackNukeShotExporterPreset(NukeShotPreset, FtrackBase):
    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        super(FtrackNukeShotExporterPreset, self).__init__(name, properties, task)

        # Set any preset defaults here
        self.properties()["enable"] = True
        self.properties()["readPaths"] = []
        self.properties()["writePaths"] = []
        self.properties()["collateTracks"] = False
        self.properties()["collateShotNames"] = False
        self.properties()["annotationsPreCompPaths"] = []
        self.properties()["includeAnnotations"] = False
        self.properties()["showAnnotations"] = True
        self.properties()["includeEffects"] = True

        # If True, tracks other than the master one will not be connected to the write node
        self.properties()["connectTracks"] = False

        # Asset properties
        self.properties()["useAssets"] = True
        self.properties()["publishScript"] = True

        # Not exposed in UI
        self.properties()["collateSequence"] = False  # Collate all trackitems within sequence
        self.properties()["collateCustomStart"] = True  # Start frame is inclusive of handles

        self.properties()["additionalNodesEnabled"] = False
        self.properties()["additionalNodesData"] = []
        self.properties()["method"] = "Blend"

        # Add property to control whether the exporter does a postProcessScript call.
        # This is not in the UI, and is only changed by create_comp.  See where this is accessed
        # in _taskStep() for more details.
        self.properties()["postProcessScript"] = True

        # Update preset with loaded data
        self.properties().update(properties)


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackBase):
    def __init__(self, preset):
        super(FtrackNukeShotExporterUI, self).__init__(preset)
        self._displayName = "Ftrack Nuke Shot File"
        self._taskType = FtrackNukeShotExporter
        self._nodeSelectionWidget = None

    def populateUI(self, widget, exportTemplate):

        if not exportTemplate:
            return

        self._exportTemplate = exportTemplate

        layout = widget.layout()
        self.createNodeSelectionWidget(layout, exportTemplate)

        properties = self._preset.properties()

        layout = QtWidgets.QFormLayout()

        self._readList = QtWidgets.QListView()
        self._writeList = QtWidgets.QListView()

        self._readList.setMinimumHeight(50)
        self._writeList.setMinimumHeight(50)
        self._readList.resize(200,50)
        self._writeList.resize(200,50)


        self._readModel = QtGui.QStandardItemModel()
        self._writeModel = QtGui.QStandardItemModel()

        # Default to the empty item unless the preset has a value set.
        for model, presetValue in ((self._readModel, properties["readPaths"]), (self._writeModel, properties["writePaths"])):
            for path, preset in exportTemplate.flatten():

                if model is self._writeModel:
                    if not hasattr(preset._parentType, 'nukeWriteNode'):
                        continue

                item = QtGui.QStandardItem(path)
                item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)

                item.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
                if path in presetValue:
                    item.setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)

                model.appendRow(item)

        self._readList.setModel(self._readModel)
        self._writeList.setModel(self._writeModel)

        readNodeListToolTip = """Select multiple entries within the shot template to be used as inputs for the read nodes (i.e. symlink, transcode.. etc).\n No selection will mean that read nodes are created in the nuke script pointing directly at the source media.\n"""
        writeNodeListToolTip = """Add one or more "Nuke Write Node" tasks to your export structure to define the path and codec settings for the nuke script.\nIf no write paths are selected, no write node will be added to the nuke script."""

        self._readList.setToolTip(readNodeListToolTip)
        self._writeList.setToolTip(writeNodeListToolTip)
        self._readModel.dataChanged.connect(self.readPresetChanged)

        publishScriptTip = """When enabled, if there is a known shot in the asset that matches the shot in Hiero, the Nuke script will be published there."""
        key, value, label = "publishScript", True, "{publish} Script"
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label=label, tooltip=publishScriptTip)
        self._uiProperties.append(uiProperty)
        layout.addRow(uiProperty._label + ":", uiProperty)

        ## @todo Think of a better name
        useAssetsTip = """If enabled, any Clips that point to managed Assets will reference the Asset, rather than their files."""
        key, value, label = "useAssets", True, "Use Assets"
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label=label, tooltip=useAssetsTip)
        self._uiProperties.append(uiProperty)
        layout.addRow(uiProperty._label + ":", uiProperty)

        layout.addRow("Read Nodes:", self._readList)
        self._writeModel.dataChanged.connect(self.writePresetChanged)
        layout.addRow("Write Nodes:", self._writeList)


        retimeToolTip = """Sets the retime method used if retimes are enabled.\n-Motion - Motion Estimation.\n-Blend - Frame Blending.\n-Frame - Nearest Frame"""
        key, value = "method", ("None", "Motion", "Frame", "Blend")
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label="Retime Method", tooltip=retimeToolTip)
        self._uiProperties.append(uiProperty)
        layout.addRow(uiProperty._label + ":", uiProperty)


        collateTracksToolTip = """Enable this to include other shots which overlap the sequence time of each shot within the script. Cannot be enabled when Read Node overrides are set."""

        key, value, label = "collateTracks", False, "Collate Shot Timings"
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=collateTracksToolTip)
        layout.addRow(label+":", uiProperty)
        self._uiProperties.append(uiProperty)
        self._collateTimeProperty = uiProperty

        collateShotNameToolTip = """Enable this to include other shots which have the same name in the Nuke script. Cannot be enabled when Read Node overrides are set."""
        key, value, label = "collateShotNames", False, "Collate Shot Name"
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset.properties(), label=label+":", tooltip=collateShotNameToolTip)
        layout.addRow(label+":", uiProperty)
        self._collateNameProperty = uiProperty
        self._uiProperties.append(uiProperty)
        self.readPresetChanged(None, None)

        additionalNodesToolTip = """When enabled, allows custom Nuke nodes to be added into Nuke Scripts.\n Click Edit to add nodes on a per Shot, Track or Sequence basis.\n Additional Nodes can also optionally be filtered by Tag."""

        additionalNodesLayout = QtWidgets.QHBoxLayout()
        additionalNodesCheckbox = QtWidgets.QCheckBox()
        additionalNodesCheckbox.setToolTip(additionalNodesToolTip)
        additionalNodesCheckbox.stateChanged.connect(self._additionalNodesEnableClicked)
        if self._preset.properties()["additionalNodesEnabled"]:
            additionalNodesCheckbox.setCheckState(QtCore.Qt.Checked)
        additionalNodesButton = QtWidgets.QPushButton("Edit")
        additionalNodesButton.setToolTip(additionalNodesToolTip)
        additionalNodesButton.clicked.connect(self._additionalNodesEditClicked)
        additionalNodesLayout.addWidget(additionalNodesCheckbox)
        additionalNodesLayout.addWidget(additionalNodesButton)
        layout.addRow("Additional Nodes:", additionalNodesLayout)

        widget.setLayout(layout)


hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerTaskUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
