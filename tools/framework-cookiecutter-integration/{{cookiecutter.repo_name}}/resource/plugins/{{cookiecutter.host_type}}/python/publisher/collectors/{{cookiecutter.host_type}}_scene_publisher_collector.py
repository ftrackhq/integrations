# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

# import maya.cmds as cmds

import ftrack_api

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import utils as {{cookiecutter.host_type}}_utils

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin


class {{cookiecutter.host_type_capitalized}}ScenePublisherCollectorPlugin(plugin.{{cookiecutter.host_type_capitalized}}PublisherCollectorPlugin):
    plugin_name = '{{cookiecutter.host_type}}_scene_publisher_collector'

    def run(self, context_data=None, data=None, options=None):
        '''Collect {{cookiecutter.host_type_capitalized}} scene name, save to temp if unsaved'''
        export_option = options.get("export")
        if export_option and isinstance(export_option, list):
            export_option = export_option[0]
        if export_option == 'scene':
            # scene_name = cmds.file(q=True, sceneName=True)
            if len(scene_name or '') == 0:
                # Scene is not saved, save it first.
                self.logger.warning('{{cookiecutter.host_type_capitalized}} not saved, saving locally')
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
    plugin = {{cookiecutter.host_type_capitalized}}ScenePublisherCollectorPlugin(api_object)
    plugin.register()
