import tempfile
import copy
from hiero.exporters.FnSubmission import Submission


class FtrackReviewable(object):
    def __init__(self, initDict):

        self.reviwable_out_path = None
        self._reviwableTask = None
        if self._submission is not None:

            start, end = self.outputRange()
            submissionDict = copy.copy(initDict)
            submissionDict['startFrame'] = start
            submissionDict['endFrame'] = end
            self._reviewableScript = tempfile.NamedTemporaryFile(prefix='ftrack_reviwable', suffix='.nk', delete=False).name
            # Create a job on our submission to do the actual rendering.
            self._reviwableTask = self._submission.addJob(Submission.kNukeRender, submissionDict, self._reviewableScript)

    def addWriteNodeToScript(self, script, rootNode, framerate):
        """ Build Write node from transcode settings and add it to the script. """
        try:
            writeNode = self.nukeWriteReviewNode(framerate, project=self._project)
        except RuntimeError as e:
            # Failed to generate write node, set task error in export queue
            # Most likely because could not map default colourspace for format settings.
            self.setError(str(e))
            return

        # The 'read_all_lines' knob controls whether input frames are read line by line or in one go,
        # so needs to be set to match the readAllLinesForExport property.
        readAllLines = self._preset.properties()["readAllLinesForExport"]
        writeNode.setKnob("read_all_lines", readAllLines)

        if self._audioFile:
            # If the transcode format supports audio (e.g. QuickTime), add the path to
            # the audio file knob
            if self._preset.fileTypeSupportsAudio():
                writeNode.setKnob("audiofile", self._audioFile)
                presetproperties = self._preset.properties()
                filetype = presetproperties["file_type"]

        # Add Write node to the script
        script.addNode(writeNode)

        # Set the knob so the Root node has the name of the Write node for viewing
        # on the timeline.  This allows for reading the script as a comp clip
        rootNode.setKnob(nuke.RootNode.kTimelineWriteNodeKnobName, writeNode.knob("name"))

    def nukeWriteReviewNode(self, framerate=None, project=None):
        """Return a Nuke Write node for this tasks's export path."""
        nodeName = None

        submissionDict = self._preset
        self.logger.info(submissionDict)

        presetProperties = self._preset.properties()
        if "writeNodeName" in presetProperties and presetProperties["writeNodeName"]:
            nodeName = self.resolvePath(presetProperties["writeNodeName"])

        self.reviwable_out_path = tempfile.NamedTemporaryFile(prefix='ftrack_reviwable', suffix='.mp4', delete=False).name

        return createWriteNode(self,
            self.reviwable_out_path,
            submissionDict,
            nodeName,
            framerate=framerate,
            project=project
        )

    def buildScript(self):
        # Generate a nuke script to render.
        script = nuke.ScriptWriter()
        self._ftrack_reviewable_script = script

        writingTrackItem = isinstance(self._item, hiero.core.TrackItem)
        writingClip = isinstance(self._item, hiero.core.Clip)
        writingSequence = isinstance(self._item, hiero.core.Sequence)

        assert (writingTrackItem or writingClip or writingSequence)

        # Export an individual clip or track item
        if writingClip or writingTrackItem:
            self.writeClipOrTrackItemToScript(script)

        # Export an entire sequence
        elif writingSequence:
            self.writeSequenceToScript(script)

        # Layout the script
        FnScriptLayout.scriptLayout(script)

    # And finally, write out the script (next to the output files).
    def writeScript(self):
        self._ftrack_reviewable_script.writeToDisk(self._reviewableScript)

    def startTask(self):
        # Write our Nuke script
        self.buildScript()
        self.writeScript()

        try:
            if self._reviwableTask:
                self._reviwableTask.startTask()
                if self._reviwableTask.error():
                    self.setError(self._reviwableTask.error())
        except Exception as e:
            if self._reviwableTask and self._reviwableTask.error():
                self.setError(self._reviwableTask.error())

    def finishTask(self):
        if self._reviwableTask:
            self._reviwableTask.finishTask()

        self.logger.info(self.reviwable_out_path)

