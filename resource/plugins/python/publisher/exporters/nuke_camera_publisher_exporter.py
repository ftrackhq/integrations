# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os
import clique
import tempfile

from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils

import nuke


class NukeCameraPublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    '''Nuke camera exporter plugin'''

    plugin_name = 'nuke_camera_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export collected Nuke camera to a file based collected object in *data* and *options*'''
        file_type = options['file_type']

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        node_name = collected_objects[0]
        cam_node = nuke.toNode(node_name)
        scene_node = write_geo_node = None

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.{}'.format(file_type)
        ).name

        try:
            scene_node = nuke.nodes.Scene()
            scene_node.setInput(0, cam_node)
            write_geo_node = nuke.nodes.WriteGeo()
            write_geo_node['file_type'].setValue(file_type)
            write_geo_node.setInput(0, scene_node)

            write_geo_node['file'].fromUserText(new_file_path)
            nuke.execute(
                write_geo_node,
                int(nuke.root()["first_frame"].getValue()),
                int(nuke.root()["last_frame"].getValue()),
                1,
            )
        finally:
            if scene_node:
                nuke.delete(scene_node)
            if write_geo_node:
                nuke.delete(write_geo_node)

        return [str(new_file_path)]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeCameraPublisherExporterPlugin(api_object)
    plugin.register()
