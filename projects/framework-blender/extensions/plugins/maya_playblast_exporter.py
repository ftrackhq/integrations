# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import glob
import platform
import bpy

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class BlenderPlayblastExporterPlugin(BasePlugin):
    name = 'blender_playblast_exporter'

    def run(self, store):
        '''
        Create a playblast from the selected camera given in the *store*.
        Save it to a temp file and this one will be published as reviewable.
        '''
        component_name = self.options.get('component')
        camera_name = store['components'][component_name].get('camera_name')

        store['components'][component_name]['exported_path'] = 'full_path'
