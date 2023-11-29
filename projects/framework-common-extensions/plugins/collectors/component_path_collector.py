# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class ComponentPathCollectorPlugin(BasePlugin):
    name = 'component_path_collector'

    def ui_hook(self, payload):
        '''
        if payload['context_type'] is 'asset': return all Assets on the given
        payload['context_id'] with asset type payload['asset_type_name']

        if payload['context_type'] is 'asset_version': return all
        AssetVersion entities available on the given
        payload['asset_id'] on task payload['context_id']
        '''

        context_id = payload['context_id']
        # Determine if we have a task or not
        context = self.session.get('Context', context_id)
        # If it's a fake asset, context will be None so return empty list.
        if not context:
            return []

        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                payload['asset_type_name']
            )
        ).one()

        if context.entity_type == 'Task':
            asset_versions = self.session.query(
                'select asset.name, asset_id, id, date, version, '
                'is_latest_version, thumbnail_url, user.first_name, '
                'user.last_name, date from AssetVersion where '
                'task_id is {} and asset.type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        else:
            asset_versions = self.session.query(
                'select asset.name, asset_id, id, date, version, '
                'is_latest_version, thumbnail_url, user.first_name, '
                'user.last_name, date from AssetVersion where '
                'parent.id is {} and asset.type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()

        with self.session.auto_populating(False):
            result = {}
            for asset_version in asset_versions:
                if asset_version['asset_id'] not in list(result.keys()):
                    result[asset_version['asset_id']] = {
                        'name': asset_version['asset']['name'],
                        'versions': [],
                    }

                result[asset_version['asset_id']]['versions'].append(
                    {
                        'id': asset_version['id'],
                        'date': asset_version['date'],
                        'version': asset_version['version'],
                        'is_latest_version': asset_version[
                            'is_latest_version'
                        ],
                        'thumbnail': asset_version['thumbnail_url']['url'],
                        'server_url': self.session._server_url,
                        'user_first_name': asset_version['user']['first_name'],
                        'user_last_name': asset_version['user']['last_name'],
                    }
                )
        return result

    def run(self, store):
        '''
        Store location path from the :obj:`self.options['asset_versions']`.

        ['asset_versions']: expected a list of dictionaries
        containing 'asset_version_id' and 'component_name' for the desired
        assets to open.
        '''

        component = self.session.query(
            'select id from Component where version_id is {} '
            'and name is {}'.format(
                self.options.get('asset_version_id'),
                self.options.get('component'),
            )
        ).first()
        if not component:
            message = (
                'Component name {} not available for '
                'asset version id {}'.format(
                    self.options.get('component_name'),
                    self.options.get('asset_version_id'),
                )
            )
            self.logger.warning(message)
            self.message = message
            self.status = constants.status.ERROR_STATUS

        location = self.session.pick_location()
        component_path = location.get_filesystem_path(component)
        component_name = self.options.get('component', 'main')
        store['components'][component_name]['collected_path'] = component_path
