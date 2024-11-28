# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from pymxs import runtime as rt


class MaxSceneExporterPlugin(BasePlugin):
    name = 'max_scene_exporter'

    def run(self, store):
        '''
        If export type is selection then export the selection objects in the
        scene with the options passed. Otherwise, set the current scene path to
        the store.
        '''
        component_name = self.options.get('component')

        export_type = store['components'][component_name].get('export_type')
        scene_name = store['components'][component_name].get('scene_name')

        exported_path = None

        if export_type == 'selection':
            try:
                exported_path = get_temp_path(filename_extension='max')
                success = rt.saveNodes(rt.selection, exported_path)
                if success:
                    self.logger.debug(
                        f'Selected objects exported to: {exported_path}.'
                    )
                else:
                    raise
            except Exception as error:
                raise PluginExecutionError(
                    message=f'Couldn\'t export selection, error:{error}'
                )

        else:
            exported_path = scene_name

        store['components'][component_name]['exported_path'] = exported_path
