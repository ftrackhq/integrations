# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import unreal

import ftrack_api

from ftrack_connect_pipeline_unreal import utils as unreal_utils
from ftrack_connect_pipeline_unreal import plugin


class UnrealSequencePublisherExporterPlugin(
    plugin.UnrealPublisherExporterPlugin
):
    '''Unreal image sequence exporter plugin'''

    plugin_name = 'unreal_sequence_publisher_exporter'

    _standard_structure = ftrack_api.structure.standard.StandardStructure()

    def run(self, context_data=None, data=None, options=None):
        '''Pick up an existing file image sequence, or render images from level sequence, given
        in *data* with the given *options*.'''

        image_sequence_path = None
        for collector in data:
            for result in collector['result']:
                for key, value in result.items():
                    if key == 'image_sequence_path':
                        image_sequence_path = value

        return [image_sequence_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    output_plugin = UnrealSequencePublisherExporterPlugin(api_object)
    output_plugin.register()
