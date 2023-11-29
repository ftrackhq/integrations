# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin


class StoreAssetContextPlugin(BasePlugin):
    name = 'store_asset_context'

    def ui_hook(self, payload):
        '''
        Return all assets based on context_id passed with *payload*.
        '''
        context_id = payload['context_id']

        asset_type_entity = self.session.query(
            'select name from AssetType where short is "{}"'.format(
                payload['asset_type_name']
            )
        ).first()

        # Determine if we have a task or not
        context = self.session.get('Context', context_id)
        # If it's a fake asset, context will be None so return empty list.
        if not context:
            return []
        if context.entity_type == 'Task':
            assets = self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where versions.task.id is {} and type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        else:
            assets = self.session.query(
                'select name, versions.task.id, type.id, id, latest_version,'
                'latest_version.version '
                'from Asset where parent.id is {} and type.id is {}'.format(
                    context_id, asset_type_entity['id']
                )
            ).all()
        result = list(assets)
        return [entity['id'] for entity in result]

    def run(self, store):
        '''
        Store values of the :obj:`self.options`
        'context_id', 'asset_name', 'comment', 'status_id' keys in the
        given *store*
        '''
        keys = [
            'context_id',
            'asset_name',
            'comment',
            'status_id',
            'asset_id',
            'asset_type_name',
        ]
        for k in keys:
            if self.options.get(k):
                store[k] = self.options.get(k)
