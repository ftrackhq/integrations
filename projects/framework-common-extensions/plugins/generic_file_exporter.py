# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os.path
import shutil

from ftrack_framework_core.plugin import BasePlugin


class GenericFileExporterPlugin(BasePlugin):
    name = 'generic_file_exporter'

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

    def rename(self, origin_path, destination_path):
        '''
        Rename the given *origin_path* to *destination_path*
        '''
        return shutil.copy(origin_path, os.path.expanduser(destination_path))

    def run(self, store):
        '''
        Expects collected_path in the <component_name> key of the given *store*
        and an export_destination from the :obj:`self.options`.
        '''
        component_name = self.options.get('component')

        collected_path = store['components'][component_name]['collected_path']
        export_destination = self.options['export_destination']

        store['components'][component_name]['exported_path'] = self.rename(
            collected_path, export_destination
        )
        self.logger.debug(f"Copied {collected_path} to {export_destination}.")
