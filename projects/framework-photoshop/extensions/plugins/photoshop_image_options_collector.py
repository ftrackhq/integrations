# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os

from ftrack_utils.paths import get_temp_path
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError

from ftrack_framework_photoshop.rpc_cep import JavascriptRPC


class PhotoshopImageOptionsCollectorPlugin(BasePlugin):
    name = 'photoshop_image_options_collector'

    def run(self, store):
        '''
        Collect the selected image format and save in the given *store* on
        "export_type"
        '''

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['export_type'] = self.options[
            'export_type'
        ]
