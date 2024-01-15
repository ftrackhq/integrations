# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class MayaSceneCollectorPlugin(BasePlugin):
    name = 'maya_scene_collector'

    def run(self, store):
        '''
        Store location path from the :obj:`self.options['asset_versions']`.

        ['asset_versions']: expected a list of dictionaries
        containing 'asset_version_id' and 'component_name' for the desired
        assets to open.
        '''
        try:
            export_type = self.options['export_type']
            extension_format = self.options['extension_format']
        except Exception as error:
            raise PluginExecutionError(
                f"Provide export_type and extension_format: {error}"
            )

        component_name = self.options.get('component', 'main')
        store['components'][component_name]['export_type'] = export_type
        store['components'][component_name][
            'extension_format'
        ] = extension_format
