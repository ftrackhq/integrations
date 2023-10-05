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
            required_output_type=str,
            required_output_value=None,
        )
        self.register_method(
            method_name='fetch',
            required_output_type=list,
            required_output_value=None,
        )

    def fetch(self, context_data=None, data=None, options=None):
        latest_asset_versions = self.session.query(
            "select asset from AssetVersion where task_id is {} and "
            "is_latest_version is True".format(
                context_data.context_id
            )
        )

        return list(latest_asset_versions)
    def run(self, context_data=None, data=None, options=None):
        '''
        From open snapshot component from the given asset_versions
        '''
        asset_versions = options.get('asset_versions')
        for asset_version in asset_versions:
            # TODO: pick the path from the snapshot component
        return ""
