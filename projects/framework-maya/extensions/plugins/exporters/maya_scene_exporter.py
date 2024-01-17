# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import maya.cmds as cmds

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaSceneExporterPlugin(BasePlugin):
    name = 'maya_scene_exporter'

    def run(self, store):
        '''
        If export type is selection then export the selection objects in the
        scene with the options passed. Otherwise, set the current scene path to
        the store.
        '''
        component_name = self.options.get('component')
        export_type = store['components'][component_name].get('export_type')
        extension_format_short = store['components'][component_name].get(
            'extension_format'
        )
        extension_format = (
            'mayaAscii' if extension_format_short == 'ma' else 'mayaBinary'
        )

        if export_type == 'selection':
            try:
                # Save file to a temp file
                exported_path = get_temp_path(
                    filename_extension=extension_format
                )
                cmds.file(
                    exported_path,
                    op='v=0',
                    exportSelected=True,
                    exportAll=False,
                    force=True,
                    type=extension_format,
                    constructionHistory=self.options['constructionHistory'],
                    channels=self.options['channels'],
                    preserveReferences=self.options['preserveReferences'],
                    shader=self.options['shader'],
                    constraints=self.options['constraints'],
                    expressions=self.options['expressions'],
                )
            except Exception as error:
                raise PluginExecutionError(
                    message=f"Couldn't export selection, error:{error}"
                )

        else:
            exported_path = cmds.file(q=True, sceneName=True)

        store['components'][component_name]['exported_path'] = exported_path
