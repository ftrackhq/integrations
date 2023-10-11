# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class ComponentPathCollectorPlugin(BasePlugin):
    name = 'component_path_collector'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_COLLECTOR_TYPE
    '''Return the full path of the file passed in the options'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None,
        )
        self.register_method(
            method_name='fetch',
            required_output_type=list,
            required_output_value=None,
        )

    def fetch(self, context_data=None, data=None, options=None):
        '''
        Return all AssetVersion entities available on the given context id
        *context_data*: expects a dictionary with the desired 'context_id'
        '''
        latest_asset_versions = self.session.query(
            "select asset from AssetVersion where task_id is {} and "
            "is_latest_version is True".format(context_data['context_id'])
        )

        return list(latest_asset_versions)

    def run(self, context_data=None, data=None, options=None):
        '''
        Return location path from the given *options['asset_versions']*.

        *options*: ['asset_versions']: expected a list of dictionaries
        containing 'asset_version_id' and 'component_name' for the desired
        assets to open.
        '''
        unresolved_asset_messages = []
        collected_paths = []
        asset_versions = options.get('asset_versions')
        for asset_version_dict in asset_versions:
            component = self.session.query(
                "select id from Component where version_id is {} "
                "and name is {}".format(
                    asset_version_dict['asset_version_id'],
                    asset_version_dict['component_name'],
                )
            ).first()
            if not component:
                message = (
                    'Component name {} not available for '
                    'asset version id {}'.format(
                        asset_version_dict['component_name'],
                        asset_version_dict['asset_version_id'],
                    )
                )
                self.logger.warning(message)
                unresolved_asset_messages.append(message)
                continue
            location = self.session.pick_location()
            component_path = location.get_filesystem_path(component)
            collected_paths.append(component_path)
        if not collected_paths:
            self.message = "\n".join(unresolved_asset_messages)
            self.status = constants.status.ERROR_STATUS

        return collected_paths
