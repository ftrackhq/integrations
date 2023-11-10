# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class ComponentPathCollectorPlugin(BasePlugin):
    name = 'component_path_collector'

    def ui_hook(self, payload):
        '''
        Return all AssetVersion entities available on the given
        *payload['context id']*
        '''
        latest_asset_versions = self.session.query(
            "select asset from AssetVersion where task_id is {} and "
            "is_latest_version is True".format(payload['context_id'])
        )

        return list(latest_asset_versions)

    def run(self, store):
        '''
        Store location path from the :obj:`self.options['asset_versions']`.

        ['asset_versions']: expected a list of dictionaries
        containing 'asset_version_id' and 'component_name' for the desired
        assets to open.
        '''
        unresolved_asset_messages = []
        collected_paths = []
        asset_versions = self.options.get('asset_versions')
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

        store['collected_paths'] = collected_paths
