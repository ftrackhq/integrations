# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

# import maya.cmds as cmds

import ftrack_api

from ftrack_connect_pipeline_{{cookiecutter.host_type}}.utils import custom_commands as {{cookiecutter.host_type}}_utils

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin


class {{cookiecutter.host_type|capitalize}}ScenePublisherCollectorPlugin(plugin.{{cookiecutter.host_type|capitalize}}PublisherCollectorPlugin):
    plugin_name = '{{cookiecutter.host_type}}_scene_publisher_collector'

    def run(self, context_data=None, data=None, options=None):
        export_option = options.get("export", 'scene')
        if export_option == 'scene':
            # scene_name = cmds.file(q=True, sceneName=True)
            if len(scene_name or '') == 0:
                # Scene is not saved, save it first.
                self.logger.warning('{{cookiecutter.host_type|capitalize}} not saved, saving locally')
                save_path, message = {{cookiecutter.host_type}}_utils.save(
                    context_data['context_id'], self.session
                )
                if not message is None:
                    self.logger.info(message)
                # scene_name = cmds.file(q=True, sceneName=True)
            if len(scene_name or '') == 0:
                self.logger.error(
                    "Error exporting the scene: Please save the scene with a "
                    "name before publish"
                )
                return []
            export_object = [scene_name]
        else:
            # export_object = cmds.ls(sl=True)
        return export_object


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type|capitalize}}ScenePublisherCollectorPlugin(api_object)
    plugin.register()
