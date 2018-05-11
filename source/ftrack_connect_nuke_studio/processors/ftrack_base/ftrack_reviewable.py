import tempfile
import copy
import sys
import json
import logging


import hiero
import hiero.core.nuke as nuke

from hiero.exporters.FnExternalRender import createWriteNode
from hiero.exporters.FnSubmission import Submission
from hiero.exporters import FnScriptLayout


class FtrackReviewable(object):
    def __init__(self, initDict):
        super(FtrackReviewable, self).__init__(initDict)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def addWriteNodeToScript(self, script, rootNode, framerate):
        """ Build Write node from transcode settings and add it to the script. """

        try:
            writeNode = self.nukeWriteReviewNode(framerate, project=self._project)
        except RuntimeError as e:
            # Failed to generate write node, set task error in export queue
            # Most likely because could not map default colourspace for format settings.
            self.setError(str(e))
            return

        self.logger.info('ADD {} WRITE NODE'.format(writeNode))

        # The 'read_all_lines' knob controls whether input frames are read line by line or in one go,
        # so needs to be set to match the readAllLinesForExport property.
        readAllLines = self._preset.properties()["readAllLinesForExport"]
        writeNode.setKnob("read_all_lines", readAllLines)

        # Add Write node to the script
        script.addNode(writeNode)


    def nukeWriteReviewNode(self, framerate=None, project=None):

        """Return a Nuke Write node for this tasks's export path."""
        self.tempmov = tempfile.NamedTemporaryFile(suffix='.mov', delete=False).name

        nodeName = 'Ftrack Reviewable Output'

        submissionDict = self._preset
        presetProperties = submissionDict.properties()
        self.original_preset_data = presetProperties.copy()

        presetProperties['file_type'] = 'mov'
        presetProperties['writeNodeName'] = nodeName
        presetProperties.setdefault('writePaths', [])
        presetProperties['writePaths'].append(self.tempmov )

        presetProperties['mov'] = {
            "encoder": "mov64",
            "codec": "mp4v",
        }

        return createWriteNode(self,
            self.tempmov,
            submissionDict,
            nodeName,
            framerate=framerate,
            project=project
        )

    def finishTask(self):
        version = self._component['version']
        review_component = version.create_component(
            path=self.tempmov,
            data={
                'name': 'ftrackreview-mp4'
            },
            location=self.ftrack_server_location
        )

        start, end = self.outputRange()
        fps = self._clip.framerate().toFloat()

        review_component['metadata']['ftr_meta'] = json.dumps({
            'frameIn': start,
            'frameOut': end,
            'frameRate': fps
        })

        review_component.session.commit()
        self.logger.info('Reviewable Component {0} Published'.format(self.tempmov))
        # restore original settings
        # self.logger.info('restoring stored settings: {0}'.format(self.original_preset_data))
        self._preset.properties().update(self.original_preset_data)

