# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile
import os

import maya.cmds as cmds

from ftrack_connect_pipeline_maya import utils as maya_utils
from ftrack_connect_pipeline_maya import plugin
import ftrack_api


class MayaNativePublisherExporterPlugin(plugin.MayaPublisherExporterPlugin):
    '''Maya native binary or ASCII exporter plugin'''

    plugin_name = 'maya_native_publisher_exporter'

    extension = None
    file_type = None

    def extract_options(self, options):
        main_options = {
            'op': 'v=0',
            'constructionHistory': False,
            'channels': False,
            'preserveReferences': False,
            'shader': False,
            'constraints': False,
            'expressions': False,
            'exportSelected': True,
            'exportAll': False,
            'force': True,
            'type': 'mayaBinary',
        }
        main_options.update(
            {key: value for (key, value) in options.items() if key[0] != '_'}
        )
        return main_options

    def run(self, context_data=None, data=None, options=None):
        '''Export Maya geometry based on collected objects in *data* and *options* supplied'''

        self.file_type = options.get('type') or 'mayaBinary'
        self.extension = '.mb' if self.file_type == 'mayaBinary' else '.ma'

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=self.extension
        ).name

        collected_objects = []
        is_scene_publish = False
        for collector in data:
            collected_objects.extend(collector['result'])
            if collector.get('options', {}).get('export') == 'scene':
                is_scene_publish = True

        if is_scene_publish:
            # Save entire scene
            options = {'type': self.file_type, 'save': True}
            scene_name = cmds.file(q=True, sceneName=True)
            if len(scene_name or '') == 0:
                # Scene is not saved, save it first. Should have been taken
                # care of by scene collector.
                self.logger.warning('Maya not saved, saving locally..')
                save_path, message = maya_utils.save_file(
                    context_data['context_id'], self.session
                )
                if not message is None:
                    self.logger.info(message)
                scene_name = cmds.file(q=True, sceneName=True)
            cmds.file(rename=new_file_path)
            cmds.file(**options)
            cmds.file(rename=scene_name)
        else:
            # Export a subset of the scene
            options = self.extract_options(options)
            self.logger.debug(
                'Calling exporters options: data {}. options {}'.format(
                    collected_objects, options
                )
            )
            cmds.select(collected_objects, r=True)
            cmds.file(new_file_path, **options)

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    output_plugin = MayaNativePublisherExporterPlugin(api_object)
    output_plugin.register()
