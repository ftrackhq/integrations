# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

import tempfile

import nuke
import nukescripts

from ftrack_connect_pipeline_nuke import plugin


class NukeDefaultPublisherExporterPlugin(plugin.NukePublisherExporterPlugin):
    plugin_name = 'nuke_default_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.nk'
        ).name

        collected_objects = []
        is_scene_publish = False
        for collector in data:
            collected_objects.extend(collector['result'])
            if collector.get('options', {}).get('export') == 'scene':
                is_scene_publish = True

        if is_scene_publish:
            self.logger.debug(
                'Publishing nuke scene to: "{}"'.format(new_file_path)
            )
            nuke.scriptSave(new_file_path)
        else:
            # Select the nodes to export
            nukescripts.clear_selection_recursive()
            for node_name in collected_objects:
                n = nuke.toNode(node_name)
                if n:
                    n.setSelected(True)
            self.logger.debug(
                'Saving selected nuke nodes to: "{}"'.format(new_file_path)
            )
            nuke.nodeCopy(new_file_path)

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeDefaultPublisherExporterPlugin(api_object)
    plugin.register()
