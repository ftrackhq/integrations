# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import maya.cmds as cmds

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaSceneLoaderPlugin(BasePlugin):
    name = 'maya_scene_loader'

    def run(self, store):
        '''
        Set the selected camera name to the *store*
        '''
        load_type = self.options.get('load_type')
        if not load_type:
            raise PluginExecutionError(
                f"Invalid load_type option expected import or reference but "
                f"got: {load_type}"
            )

        component_path = store.get('component_path')
        if not component_path:
            raise PluginExecutionError(f'No component path provided in store!')

        if load_type == 'import':
            try:
                cmds.file(
                    component_path,
                    i=True,
                    namespace=self.options.get('namespace', ''),
                )
            except RuntimeError as error:
                raise PluginExecutionError(
                    f"Failed to import {component_path} to scene. Error: {error}"
                )
        elif load_type == 'reference':
            try:
                cmds.file(
                    component_path,
                    r=True,
                    namespace=self.options.get('namespace', ''),
                )
            except RuntimeError as error:
                raise PluginExecutionError(
                    f"Failed to reference {component_path} to scene. Error: {error}"
                )

        self.logger.debugf(
            f"Component {component_path} has been loaded to scene."
        )
