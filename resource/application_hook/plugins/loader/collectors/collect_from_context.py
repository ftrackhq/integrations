# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin

class CollectFromContextPlugin(plugin.LoaderCollectorPlugin):
    plugin_name = 'collect_from_context'

    def run(self, context=None, data=None, options=None):
        version_id = context.get('version_id', [])
        asset_version = self.session.get(
            'AssetVersion', version_id
        )
        accepted_formats = options.get('accepted_formats', [])
        component_list = options.get('component_list', ['main'])
        location = self.session.pick_location()
        component_paths = []
        for component in asset_version['components']:
            if component['name'] in component_list:
                component_path = location.get_filesystem_path(component)
                if accepted_formats and os.path.splitext(component_path)[
                                                -1] not in accepted_formats:
                    self.logger.warning(
                        '{} not among accepted format {}'.format(
                            component_path, accepted_formats
                        ))
                    continue
                component_paths.append(component_path)

        return component_paths


def register(api_object, **kw):
    plugin = CollectFromContextPlugin(api_object)
    plugin.register()
