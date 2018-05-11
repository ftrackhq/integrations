import logging
import tempfile
from hiero.exporters.FnExternalRender import createWriteNode


class FtrackReviewable(object):
    def __init__(self, initDict):
        super(FtrackReviewable, self).__init__(initDict)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.is_enabled = self._preset.properties()['ftrack']['opt_publish_review']

    def addWriteNodeToScript(self, script, rootNode, framerate):
        """ Build Write node from transcode settings and add it to the script. """

        if not self.is_enabled:
            return

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

        # Add Write node to the script
        script.addNode(writeNode)


    def nukeWriteReviewNode(self, framerate=None, project=None):
        """Return a Nuke Write node for this tasks's export path."""
        self.tempmov = tempfile.NamedTemporaryFile(suffix='.mov', delete=False).name

        node_name = 'Ftrack Reviewable Output'

        submissionDict = self._preset
        presetProperties = submissionDict.properties()
        self.original_preset_data = presetProperties.copy()

        presetProperties['file_type'] = 'mov'
        presetProperties['writeNodeName'] = node_name
        presetProperties.setdefault('writePaths', [])
        presetProperties['writePaths'].append(self.tempmov )

        presetProperties['mov'] = {
            "encoder": "mov64",
            "codec": "avc1\tH.264",
            "quality": 3,
            "settingsString": "H.264, High Quality",
            "keyframerate": 1,
        }

        return createWriteNode(self,
            self.tempmov,
            submissionDict,
            node_name,
            framerate=framerate,
            project=project
        )

    def finishTask(self):
        if not self.is_enabled:
            return

        version = self._component['version']
        review_component = version.create_component(
            path=self.tempmov,
            data={
                'name': 'preview'
            },
            location=self.ftrack_location
        )

        self.session.commit()
        self.ftrack_server_location.add_component(review_component, self.ftrack_location)
        version.encode_media(review_component)
        self.session.commit()

        self.logger.info('Reviewable Component {0} Published'.format(self.tempmov))
        # restore original settings
        # self.logger.info('restoring stored settings: {0}'.format(self.original_preset_data))
        self._preset.properties().update(self.original_preset_data)

