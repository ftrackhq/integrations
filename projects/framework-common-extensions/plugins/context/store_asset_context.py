# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginUIHookExecutionError


class StoreAssetContextPlugin(BasePlugin):
    name = 'store_asset_context'

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
        context = self.session.query(
            'select link from Context where id is {}'.format(context_id)
        ).one()
        project = self.session.query(
            'select project_schema from Project where id is "{}"'.format(
                context['link'][0]['id']
            )
        ).one()
        statuses = project['project_schema'].get_statuses('AssetVersion')
        # If it's a fake asset, context will be None so return empty list.
        if not context:
            return []

        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                payload['asset_type_name']
            )
        ).one()

        if not context.entity_type == 'Task':
            raise PluginUIHookExecutionError(
                "Query not supported on non task contexts"
            )

        # We are querying the following assets:
        # Before the "or":
        # Assets where this task has been linked to a version previously.
        # After the "or":
        # Assets belonging to the task parent (AssetBuild) with or without
        # versions (regardless if it has been linked to this task).
        assets = self.session.query(
            f'select name, id, latest_version.version, versions, versions.id, versions.date, '
            f'versions.version, versions.is_latest_version, '
            f'versions.thumbnail_url, versions.user.first_name, '
            f'versions.user.last_name, versions.status.name from Asset '
            f'where (versions.task_id is {context_id} and '
            f'type.id is {asset_type_entity["id"]}) or (parent.children.id '
            f'is {context_id} and type.id is '
            f'{asset_type_entity["id"]})'
        ).all()

        result = dict()
        result['statuses'] = []
        for status in statuses:
            result['statuses'].append(
                {
                    'id': status['id'],
                    'name': status['name'],
                    'color': status['color'],
                }
            )
        with self.session.auto_populating(False):
            result['assets'] = {}
            for asset in assets:
                if asset['id'] not in list(result['assets'].keys()):
                    result['assets'][asset['id']] = {
                        'name': asset['name'],
                        'versions': [],
                        'server_url': self.session.server_url,
                    }

                # Return info for latest version only.
                if asset['versions']:
                    latest_version = asset['versions'][-1]
                    result['assets'][asset['id']]['versions'].append(
                        {
                            'id': latest_version['id'],
                            'date': latest_version['date'].strftime(
                                '%y-%m-%d %H:%M'
                            ),
                            'version': latest_version['version'],
                            'is_latest_version': latest_version[
                                'is_latest_version'
                            ],
                            # Next available version number
                            'next_version': asset['latest_version']['version']
                            + 1,
                            'thumbnail': latest_version['thumbnail_url'][
                                'url'
                            ],
                            'user_first_name': latest_version['user'][
                                'first_name'
                            ],
                            'user_last_name': latest_version['user'][
                                'last_name'
                            ],
                            'status': latest_version['status']['name'],
                        }
                    )
        return result

    def run(self, store):
        '''
        Store values of the :obj:`self.options`
        'context_id', 'asset_name', 'comment', 'status_id' keys in the
        given *store*
        '''
        keys = [
            'context_id',
            'asset_name',
            'asset_id',
            'comment',
            'status_id',
            'asset_version_id',
            'asset_type_name',
        ]
        for k in keys:
            if self.options.get(k):
                store[k] = self.options.get(k)
