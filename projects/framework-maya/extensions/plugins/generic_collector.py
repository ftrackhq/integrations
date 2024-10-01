# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import maya.cmds as cmds

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_utils.paths import get_temp_path


class MayaGenericCollectorPlugin(BasePlugin):
    name = 'maya_generic_collector'

    def ui_hook(self, payload):
        '''
        Return the selected objects in the scene.
        '''

        selected_objects = cmds.ls(sl=True, l=True)
        result = {
            'widget': payload.get('widget'),
            'items': selected_objects,
        }
        return result

    def export_selection(self, collected_objects, extension_format='mb'):
        extension_format = (
            'mayaAscii' if extension_format == 'ma' else 'mayaBinary'
        )
        try:
            original_selection = cmds.ls(sl=True)
            selected_objects = cmds.select(collected_objects, r=True)

            # Save file to a temp file
            exported_path = get_temp_path(filename_extension=extension_format)
            cmds.file(
                exported_path,
                op='v=0',
                exportSelected=True,
                exportAll=False,
                force=True,
                type=extension_format,
                constructionHistory=True,
                channels=True,
                preserveReferences=True,
                shader=True,
                constraints=True,
                expressions=True,
            )
            self.logger.debug(
                f"Collected objects exported to: {exported_path}."
            )
            # restore selection
            cmds.select(original_selection, r=True)

            return exported_path

        except Exception as error:
            raise PluginExecutionError(
                message=f"Couldn't export collected objects, error:{error}"
            )

    def run(self, store):
        '''
        Get folder_path and file_name from the :obj:`self.options`
        and store the collected_file in the given *store*.
        '''
        components = self.options.get('components', {})
        for component_name, component_value in components.items():
            file_path = component_value.get('file_path')
            collected_objects = component_value.get('items_list')
            if not file_path and not collected_objects:
                message = (
                    "Please provide file_path or items_list in component options. \n "
                    "options: {}".format(self.options)
                )
                raise PluginExecutionError(message)
            if collected_objects:
                self.logger.debug(f"Collected objects: {collected_objects}.")
                file_path = self.export_selection(collected_objects)
            self.logger.debug(f"Collected file_path: {file_path}.")
            if store.get('components') is None:
                store['components'] = {}
            if store['components'].get(component_name) is None:
                store['components'][component_name] = {}
            store['components'][component_name]['collected_path'] = file_path
