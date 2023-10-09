# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class FtrackAssetsFetcherPlugin(BasePlugin):
    name = 'ftrack_assets_fetcher'
    host_type = constants.host.PYTHON_HOST_TYPE
    plugin_type = constants.plugin.PLUGIN_COLLECTOR_TYPE
    '''Return the full path of the file passed in the options'''

    def register_methods(self):
        self.register_method(
            method_name='run',
            required_output_type=list,
            required_output_value=None,
        )

    def run(self, context_data=None, data=None, options=None):
        '''
        Return all AssetVersion entities available on the given context id
        *context_data*: expects a dictionary with the desired 'context_id'
        '''
        latest_asset_versions = self.session.query(
            "select asset from AssetVersion where task_id is {} and "
            "is_latest_version is True".format(context_data['context_id'])
        )

        return list(latest_asset_versions)
