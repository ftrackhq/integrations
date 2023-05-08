# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
from framework_core import plugin
from framework_core.constants import asset as asset_const

import ftrack_api


class CommonContextLoaderCollectorPlugin(plugin.LoaderCollectorPlugin):
    '''Plugin that collects loader compatible component paths'''

    plugin_name = 'common_context_loader_collector'

    def run(self, context_data=None, data=None, options=None):
        '''Retrieve a list of component paths based on version id given in *context_data* matching file_type given in *options*'''

        version_id = context_data.get('version_id', [])

        asset_version_entity = self.session.query(
            'AssetVersion where id is "{}"'.format(version_id)
        ).one()

        component_name = data[0].get('name')
        file_formats = options.get('file_formats', [])
        location = self.session.pick_location()
        result = {}
        for component in asset_version_entity['components']:
            if component['name'] == component_name:
                component_path = location.get_filesystem_path(component)
                if (
                    file_formats
                    and os.path.splitext(component_path)[-1]
                    not in file_formats
                ):
                    self.logger.warning(
                        '{} not among accepted format {}'.format(
                            component_path, file_formats
                        )
                    )
                    continue
                result[asset_const.COMPONENT_NAME] = component['name']
                result[asset_const.COMPONENT_PATH] = component_path
                result[asset_const.COMPONENT_ID] = component['id']
                break

        return result


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonContextLoaderCollectorPlugin(api_object)
    plugin.register()
