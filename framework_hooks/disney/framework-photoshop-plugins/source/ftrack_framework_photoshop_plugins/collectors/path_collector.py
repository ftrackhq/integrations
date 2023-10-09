# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class PathCollectorPlugin(BasePlugin):
    name = 'path_collector'
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
        Return location path from the given *options['selected_assets']*.
        '''
        fetcher = options.get('fetcher')
        if fetcher == 'ftrack_assets_fetcher':
            return self.collect_from_ftrack_location(
                options.get('selected_assets')
            )

    def collect_from_ftrack_location(self, asset_versions):
        '''
        Return location path from the given list of *asset_versions*.

        *asset_versions*: expected a list of dictionaries
        containing 'asset_version_id' and 'component_name' for the desired
        assets to open.
        '''
        unresolved_asset_messages = []
        collected_paths = []
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
