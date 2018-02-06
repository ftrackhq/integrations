import os
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

from ftrack_base import FtrackBasePreset, FtrackBase, FtrackBaseProcessor


class FtrackNukeShotExporter(NukeShotExporter, FtrackBaseProcessor):
    def __init__(self, initDict):
        NukeShotExporter.__init__(self, initDict)
        FtrackBaseProcessor.__init__(self, initDict)

        self._nothingToDo = True
        self._tag = None
        self._tag_guid = None

        assert self.fn_mapping

    def updateItem (self, originalItem, localtime):
        """updateItem - This is called by the processor prior to taskStart, crucially on the main thread.\n
        This gives the task an opportunity to modify the original item on the main thread, rather than the clone."""

        timestamp = self.timeStampString(localtime)
        tag = hiero.core.Tag("Nuke Project File " + timestamp, "icons:Nuke.png")

        writePaths = []

        # Need to instantiate each of the selected write path tasks and resolve the path
        for (itemPath, itemPreset) in self._exportTemplate.flatten():
            for writePath in self._preset.properties()["writePaths"]:
                if writePath == itemPath:
                    # Generate a task on same items as this one but swap in the shot path that goes with this preset.
                    taskData = hiero.core.TaskData(itemPreset, self._item, self._exportRoot, itemPath, self._version, self._exportTemplate,
                                                    project=self._project, cutHandles=self._cutHandles, retime=self._retime, startFrame=self._startFrame, resolver=self._resolver, skipOffline=self._skipOffline)
                    task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)

                    resolvedPath = task.resolvedExportPath()

                    # Ensure enough padding for output range
                    output_start, output_end = task.outputRange(ignoreRetimes=False, clampToSource=False)
                    count = len(str(max(output_start, output_end)))
                    resolvedPath = hiero.core.util.ResizePadding(resolvedPath, count)

                    writePaths.append(resolvedPath)

        tag.metadata().setValue("tag.path", ";".join(writePaths))
        # Right now don't add the time to the metadata
        # We would rather store the integer time than the stringified time stamp
        # tag.setValue("time", timestamp)

        tag.metadata().setValue("tag.script", self.resolvedExportPath())
        tag.metadata().setValue("tag.localtime", str(localtime))

        start, end = self.outputRange()
        tag.metadata().setValue("tag.startframe", str(start))
        tag.metadata().setValue("tag.duration", str(end-start+1))

        if isinstance(self._item, hiero.core.TrackItem):
            tag.metadata().setValue("tag.sourceretime", str(self._item.playbackSpeed()))

        frameoffset = self._startFrame if self._startFrame else 0

        # Only if write paths have been set
        if len(writePaths) > 0:
            # Video file formats are not offset, so set frameoffset to zero
            if hiero.core.isVideoFileExtension(os.path.splitext(writePaths[0])[1].lower()):
                frameoffset = 0

        tag.metadata().setValue("tag.frameoffset", str(frameoffset))

        if self._cutHandles:
            tag.metadata().setValue("tag.handles", str(self._cutHandles))

        originalItem.addTag(tag)

        # if self._preset.properties()["useAssets"]:
        #     # Allow listeners to update the item too
        #     manager = FnAssetAPI.Events.getEventManager()
        #     manager.blockingEvent(True, 'hieroToNukeScriptUpdateTrackItem', self._item, tag)

        # The guid of the tag attached to the trackItem is different from the tag instance we created
        # Get the last tag in the list and store its guid
        self._tag = originalItem.tags()[-1]
        self._tag_guid = originalItem.tags()[-1].guid()

        FtrackBaseProcessor.updateItem(self, originalItem, localtime)

    def taskStep(self):
        # self.logger.info('TaskStep...')
        super(FtrackNukeShotExporter, self).taskStep()
        if self._nothingToDo:
            return False

        script = nuke.ScriptWriter()

        start, end = self.outputRange(ignoreRetimes=True, clampToSource=False)
        unclampedStart = start
        hiero.core.log.debug( "rootNode range is %s %s %s", start, end, self._startFrame )

        firstFrame = start
        if self._startFrame is not None:
            firstFrame = self._startFrame

        # if startFrame is negative we can only assume this is intentional
        if start < 0 and (self._startFrame is None or self._startFrame >= 0):
            # We dont want to export an image sequence with negative frame numbers
            self.setWarning("%i Frames of handles will result in a negative frame index.\nFirst frame clamped to 0." % self._cutHandles)
            start = 0
            firstFrame = 0

        # Clip framerate may be invalid, then use parent sequence framerate
        framerate = self._sequence.framerate()
        dropFrames = self._sequence.dropFrame()
        if self._clip and self._clip.framerate().isValid():
            framerate = self._clip.framerate()
            dropFrames = self._clip.dropFrame()
        fps = framerate.toFloat()
        showAnnotations = self._preset.properties()["showAnnotations"]

        # Create the root node, this specifies the global frame range and frame rate
        rootNode = nuke.RootNode(start, end, fps, showAnnotations)
        rootNode.addProjectSettings(self._projectSettings)
        #rootNode.setKnob("project_directory", os.path.split(self.resolvedExportPath())[0])
        script.addNode(rootNode)

        if isinstance(self._item, hiero.core.TrackItem):
            rootNode.addInputTextKnob("shot_guid", value=hiero.core.FnNukeHelpers._guidFromCopyTag(self._item),
                                        tooltip="This is used to identify the master track item within the script",
                                        visible=False)
            inHandle, outHandle = self.outputHandles(self._retime != True)
            rootNode.addInputTextKnob("in_handle", value=int(inHandle), visible=False)
            rootNode.addInputTextKnob("out_handle", value=int(outHandle), visible=False)

        # Set the format knob of the root node
        rootNode.setKnob("format", str(self.rootFormat()))

        # BUG 40367 - proxy_type should be set to 'scale' by default to reflect
        # the custom default set in Nuke. Sadly this value can't be queried,
        # as it's set by nuke.knobDefault, hence the hard coding.
        rootNode.setKnob("proxy_type","scale")

        # Add Unconnected additional nodes
        if self._preset.properties()["additionalNodesEnabled"]:
            script.addNode(FnExternalRender.createAdditionalNodes(FnExternalRender.kUnconnected, self._preset.properties()["additionalNodesData"], self._item))

        # Project setting for using OCIO nodes for colourspace transform
        useOCIONodes = self._project.lutUseOCIOForExport()

        useEntityRefs = self._preset.properties().get("useAssets", True)
        # A dict of arguments which are used when calling addToNukeScript on any clip/sequence/trackitem
        addToScriptCommonArgs = { 'useOCIO' : useOCIONodes,
                                'additionalNodesCallback' : self._buildAdditionalNodes,
                                'includeEffects' : self.includeEffects(),
                                'useEntityRefs': useEntityRefs}

        writeNodes = self._createWriteNodes(firstFrame, start, end, framerate, rootNode)

        # MPLEC TODO should enforce in UI that you can't pick things that won't work.
        if not writeNodes:
            # Blank preset is valid, if preset has been set and doesn't exist, report as error
            self.setWarning(str("NukeShotExporter: No write node destination selected"))

        if self.writingSequence():
            self.writeSequence(script, addToScriptCommonArgs)

        # Write out the single track item
        else:
            self.writeTrackItem(script, firstFrame)


        script.pushLayoutContext("write", "%s_Render" % self._item.name())

        metadataNode = nuke.MetadataNode(metadatavalues=[("hiero/project", self._projectName), ("hiero/project_guid", self._project.guid()), ("hiero/shot_tag_guid", self._tag_guid) ] )

        # Add sequence Tags to metadata
        metadataNode.addMetadataFromTags( self._sequence.tags() )

        # Apply timeline offset to nuke output
        if isinstance(self._item, hiero.core.TrackItem):
            if self._cutHandles is None:
                # Whole clip, so timecode start frame is first frame of clip
                timeCodeNodeStartFrame = unclampedStart
            else:
                startHandle, endHandle = self.outputHandles()
                timeCodeNodeStartFrame = trackItemTimeCodeNodeStartFrame(unclampedStart, self._item, startHandle, endHandle)
            timecodeStart = self._clip.timecodeStart()
        else:
            # Exporting whole sequence/clip
            timeCodeNodeStartFrame = unclampedStart
            timecodeStart = self._item.timecodeStart()

        script.addNode(nuke.AddTimeCodeNode(timecodeStart=timecodeStart, fps=framerate, dropFrames=dropFrames, frame=timeCodeNodeStartFrame))
        # The AddTimeCode field will insert an integer framerate into the metadata, if the framerate is floating point, we need to correct this
        metadataNode.addMetadata([("input/frame_rate",framerate.toFloat())])

        script.addNode(metadataNode)

        # Generate Write nodes for nuke renders.

        for node in writeNodes:
            script.addNode(node)

        # Check Hiero Version.
        if hiero.core.env.get('VersionMajor') < 11:  
            # add a viewer
            viewerNode = nuke.Node("Viewer")

            # Bug 45914: If the user has for some reason selected a custom OCIO config, but then set the 'Use OCIO nodes when export' option to False,
            # don't set the 'viewerProcess' knob, it's referencing a LUT in the OCIO config which Nuke doesn't know about
            setViewerProcess = True
            if not self._projectSettings['lutUseOCIOForExport'] and self._projectSettings['ocioConfigPath']:
                setViewerProcess = False

            if setViewerProcess:
                # Bug 45845 - default viewer lut should be set in the comp
                from hiero.exporters.FnNukeShotExporter import _toNukeViewerLutFormat
                viewerLut = _toNukeViewerLutFormat(self._projectSettings['lutSettingViewer'])
                viewerNode.setKnob("viewerProcess", viewerLut)
        else:
            from hiero.exporters.FnExportUtil import createViewerNode
            viewerNode = createViewerNode(self._projectSettings)

        script.addNode( viewerNode )

        # Create pre-comp nodes for external annotation scripts
        annotationsNodes = self._createAnnotationsPreComps()
        if annotationsNodes:
            script.addNode(annotationsNodes)

        scriptFilename = self.resolvedExportPath()
        hiero.core.log.debug( "Writing Script to: %s", scriptFilename )

        # Call callback before writing script to disk (see _beforeNukeScriptWrite definition below)
        self._beforeNukeScriptWrite(script)

        script.popLayoutContext()

        # Layout the script
        FnScriptLayout.scriptLayout(script)

        script.writeToDisk(scriptFilename)
        #if postProcessScript has been set to false, don't post process
        #it will be done on a background thread by create comp
        #needs to be done as part of export task so that information
        #is added in hiero workflow
        if self._preset.properties().get("postProcessScript", True):
            error = postProcessor.postProcessScript(scriptFilename)
            if error:
                hiero.core.log.error( "Script Post Processor: An error has occurred while preparing script:\n%s", scriptFilename )
        # Nothing left to do, return False.
        return False

    def finishTask(self):
        NukeShotExporter.finishTask(self) 
        FtrackBaseProcessor.finishTask(self)

    def _makePath(self):
        FtrackBaseProcessor._makePath(self)


class FtrackNukeShotExporterPreset(NukeShotPreset, FtrackBasePreset):
    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        NukeShotPreset.__init__(self, name, properties, task)
        FtrackBasePreset.__init__(self, name, properties)

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
        
    def set_ftrack_properties(self, properties):
        FtrackBasePreset.set_ftrack_properties(self, properties)
        self.properties()['ftrack'] = {}

        # add placeholders for default ftrack defaults
        self.properties()['ftrack']['task_type'] = 'Compositing'
        self.properties()['ftrack']['asset_type_code'] = 'script'
        self.properties()['ftrack']['component_pattern'] = '{shot}.{ext}'
        self.properties()['ftrack']['task_status'] = 'Not Started'
        self.properties()['ftrack']['shot_status'] = 'In progress'
        self.properties()['ftrack']['asset_version_status'] = 'WIP'
        self.properties()['ftrack']['project_schema'] = 'Film Pipeline'

    def addUserResolveEntries(self, resolver):
        FtrackBasePreset.addUserResolveEntries(self, resolver)


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackBase):
    def __init__(self, preset):
        NukeShotExporterUI.__init__(self, preset)
        FtrackBase.__init__(self, preset)

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
