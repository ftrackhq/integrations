# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

import hou


class HoudiniSceneOpenerPlugin(BasePlugin):
    name = 'houdini_scene_opener'

    def run(self, store):
        '''
        Expects collected_file in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name].get(
            'collected_path'
        )

        if not collected_path:
            raise PluginExecutionError("No path provided to open!")

        try:
            hou.hipFile.load(collected_path.replace('\\', '/'))
        except Exception as error:
            raise PluginExecutionError(
                f"Couldn't open the given path. Error: {error}"
            )

        self.logger.debug(f"Houdini scene opened. Path: {collected_path}")

        store['components'][component_name]['open_result'] = collected_path
