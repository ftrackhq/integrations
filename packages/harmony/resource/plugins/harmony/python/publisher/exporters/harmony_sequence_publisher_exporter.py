# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import tempfile
import os

import ftrack_api

from ftrack_connect_pipeline import utils as core_utils

from ftrack_connect_pipeline_harmony import utils as harmony_utils
from ftrack_connect_pipeline_harmony import plugin


class HarmonySequencePublisherExporterPlugin(
    plugin.HarmonyPublisherExporterPlugin
):
    plugin_name = 'harmony_sequence_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Have Harmony render image sequence to a temp directory'''

        destination_path = tempfile.mkdtemp()
        prefix = "image"
        extension = ".{}".format(options.get("image_format", "png"))

        client = harmony_utils.get_event_hub_client()

        self.logger.info(
            "Telling Harmony to render the current scene to {}.".format(
                destination_path
            )
        )

        reply_event = client.send(
            harmony_utils.TCPEventHubClient.TOPIC_RENDER_DO,
            {
                "pipeline": {
                    "destination_path": "{}{}".format(
                        destination_path, os.sep
                    ),
                    "prefix": prefix,
                    "extension": extension,
                }
            },
            synchronous=True,
        )

        # Store image sequence path so reviewable can pick it up later
        harmony_utils.store_image_sequence_path(destination_path, extension)

        new_file_path = core_utils.find_image_sequence(destination_path)

        self.logger.info(
            "Render done, result: {} (reply: {})".format(
                new_file_path, reply_event
            )
        )

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    output_plugin = HarmonySequencePublisherExporterPlugin(api_object)
    output_plugin.register()
