# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

import maya.cmds as cmds

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaSceneOpenerPlugin(BasePlugin):
    name = 'maya_scene_opener'

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

        if not os.path.exists(collected_path):
            raise PluginExecutionError("File does not exist!")

        try:
            cmds.file(collected_path, o=True, f=True)
        except Exception as error:
            raise PluginExecutionError(
                f"Couldn't open the given path. Error: {error}"
            )

        store['components'][component_name]['open_result'] = self.open_scene(
            collected_path
        )
