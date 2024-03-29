# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


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
        component_name = payload['component']
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

        if context.entity_type == 'Task' and not payload.get('show_all'):
            asset_versions = self.session.query(
                'select asset.name, asset_id, id, date, version, '
                'is_latest_version, thumbnail_url, user.first_name, '
                'user.last_name, date, components.name from AssetVersion where '
                'task_id is {} and asset.type.id is {} and components.name is {}'.format(
                    context_id, asset_type_entity['id'], component_name
                )
            ).all()
        elif context.entity_type == 'Task' and payload.get('show_all'):
            asset_versions = self.session.query(
                'select asset.name, asset_id, id, date, version, '
                'is_latest_version, thumbnail_url, user.first_name, '
                'user.last_name, date, components.name from AssetVersion where '
                'asset.parent.children.id is {} and asset.type.id is {} and components.name is {}'.format(
                    context_id, asset_type_entity['id'], component_name
                )
            ).all()
        else:
            asset_versions = self.session.query(
                'select asset.name, asset_id, id, date, version, '
                'is_latest_version, thumbnail_url, user.first_name, '
                'user.last_name, date, components.name from AssetVersion where '
                'parent.id is {} and asset.type.id is {} and components.name is {}'.format(
                    context_id, asset_type_entity['id'], component_name
                )
            ).all()

        result = {}
        with self.session.auto_populating(False):
            result['assets'] = {}
            for asset_version in asset_versions:
                if asset_version['asset_id'] not in list(
                    result['assets'].keys()
                ):
                    result['assets'][asset_version['asset_id']] = {
                        'name': asset_version['asset']['name'],
                        'versions': [],
                        'server_url': self.session.server_url,
                    }

                result['assets'][asset_version['asset_id']]['versions'].append(
                    {
                        'id': asset_version['id'],
                        'date': asset_version['date'].strftime(
                            '%y-%m-%d %H:%M'
                        ),
                        'version': asset_version['version'],
                        'is_latest_version': asset_version[
                            'is_latest_version'
                        ],
                        'thumbnail': asset_version['thumbnail_url']['url'],
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
        asset_version_id = self.options.get('asset_version_id')
        if not asset_version_id:
            raise PluginExecutionError('Please select a version to open')
        component_name = self.options.get('component')
        if not component_name:
            raise PluginExecutionError(
                'Please select name of component to open'
            )
        component = self.session.query(
            'select id from Component where version_id is {} '
            'and name is {}'.format(
                asset_version_id,
                component_name,
            )
        ).first()
        self.logger.debug(f"Component collected: {component}.")
        if not component:
            message = (
                'Component name {} not available for '
                'asset version id {}'.format(
                    component_name,
                    asset_version_id,
                )
            )
            self.logger.warning(message)
            raise PluginExecutionError(message=message)

        location = self.session.pick_location()
        self.logger.debug(f"Location picked: {location}.")
        component_path = location.get_filesystem_path(component)
        self.logger.debug(f"Component path: {component_path}.")
        component_name = self.options.get('component', 'main')
        store['components'][component_name]['collected_path'] = component_path
