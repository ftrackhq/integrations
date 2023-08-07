# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

from ftrack_framework_plugin import BasePlugin
from ftrack_framework_plugin import constants

#TODO: double check if this is somethign that we like to allow, or we shouldn't
# have any reference to core? (We are kind of cicling references here)
from ftrack_framework_core.constants import asset as asset_constants


class CommonContextLoaderCollectorPlugin(BasePlugin):
    '''Plugin that collects loader compatible component paths'''

    name = 'common_context_loader_collector'
    host_type = constants.hosts.PYTHON_HOST_TYPE
    plugin_type = constants.PLUGIN_COLLECTOR_TYPE

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=dict,
            required_output_value={
                asset_constants.COMPONENT_NAME: None,
                asset_constants.COMPONENT_PATH: None,
                asset_constants.COMPONENT_ID: None,
            }
        )

    def run(self, context_data=None, data=None, options=None):
        '''Retrieve a list of component paths based on version id given in *context_data* matching file_type given in *options*'''

        version_id = context_data.get('version_id', [])

        asset_version_entity = self.session.query(
            'AssetVersion where id is "{}"'.format(version_id)
        ).one()

        component_name = data[0].get('name')
        file_formats = options.get('file_formats', [])
        location = self.session.pick_location()
        result = self.methods['run']['required_output_value']
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
                result[asset_constants.COMPONENT_NAME] = component['name']
                result[asset_constants.COMPONENT_PATH] = component_path
                result[asset_constants.COMPONENT_ID] = component['id']
                break

        return result
