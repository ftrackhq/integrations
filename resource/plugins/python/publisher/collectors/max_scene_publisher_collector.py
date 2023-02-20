# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils

from ftrack_connect_pipeline_3dsmax import plugin


class MaxScenePublisherCollectorPlugin(plugin.MaxPublisherCollectorPlugin):
    plugin_name = 'max_scene_publisher_collector'

    def run(self, context_data=None, data=None, options=None):
        '''Collect Max scene name, save to temp if unsaved'''
        export_option = options.get("export")
        if export_option and isinstance(export_option, list):
            export_option = export_option[0]
        if export_option == 'scene':
            scene_name = "{}{}".format(rt.maxFilePath, rt.maxFileName)
            if len(scene_name or '') == 0:
                # Scene is not saved, save it first.
                self.logger.warning('Max scene not saved, saving locally')
                scene_name, message = max_utils.save_file(
                    None,
                    context_id=context_data['context_id'],
                    session=self.session,
                )
                if not message is None:
                    self.logger.info(message)
            if len(scene_name or '') == 0:
                return False, {
                    'message': "Error exporting the scene: Please save the scene with a "
                    "name before publish"
                }
            export_object = [scene_name]
        else:
            export_object = [node.getmxsprop('name') for node in rt.selection]
        return export_object


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxScenePublisherCollectorPlugin(api_object)
    plugin.register()
