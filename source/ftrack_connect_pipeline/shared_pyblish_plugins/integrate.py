# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import pyblish.api


class IntegratorCreateAsset(pyblish.api.ContextPlugin):
    '''Create asset and prepare publish.'''

    order = pyblish.api.IntegratorOrder

    def process(self, context):
        '''Process *context* create asset.'''
        ftrack_entity = context.data['ftrack_entity']
        session = ftrack_entity.session

        asset_type_id = context.data['options']['asset']['asset_type']
        asset_name = context.data['options']['asset']['asset_name']
        comment = context.data['options'].get('comment', '')

        if isinstance(ftrack_entity, session.types['Task']):
            parent_context_id = ftrack_entity['parent_id']
            task_id = ftrack_entity['id']
        else:
            parent_context_id = ftrack_entity['id']
            task_id = None

        asset = session.query(
            'Asset where context_id is "{0}" and name is "{1}" and '
            'type_id is "{2}"'.format(
                parent_context_id, asset_name, asset_type_id
            )
        ).first()

        self.log.debug(
            'Found asset {0!r} based on context id {1!r}, name {2!r} and type '
            '{3!r}'.format(
                asset, parent_context_id, asset_name, asset_type_id
            )
        )

        if asset is None:
            asset = session.create(
                'Asset',
                {
                    'context_id': parent_context_id,
                    'type_id': asset_type_id,
                    'name': asset_name
                }
            )
            self.log.debug(
                'Created asset with name {0!r} on {1!r}'.format(
                    asset_name, ftrack_entity
                )
            )

        # Create an asset version in a pre-published state.
        asset_version = session.create(
            'AssetVersion',
            {
                'asset': asset,
                'is_published': False,
                'comment': comment,
                'task_id': task_id
            }
        )

        session.commit()

        context.data['asset_version'] = asset_version

        self.log.debug('Created asset version {0!r}.'.format(asset_version))


class IntegratorCreateComponents(pyblish.api.InstancePlugin):
    '''Extract nuke cameras from scene.'''

    order = pyblish.api.IntegratorOrder + 0.1

    families = ['*']

    def process(self, instance):
        '''Process *instance* and create components.'''
        context = instance.context
        asset_version = context.data['asset_version']
        session = asset_version.session

        if 'location_name' in instance.data['options']:
            location = session.query(
                'Location where name is "{0}"'.format(
                    instance.data['options']['location_name']
                )
            ).one()
        else:
            location = session.pick_location()

        self.log.debug('Picked location {0!r}.'.format(location['name']))

        for component_item in instance.data.get('ftrack_components', []):
            session.create_component(
                component_item['path'],
                {
                    'version_id': asset_version['id'],
                    'name': component_item['name']
                },
                location=location
            )
            self.log.debug(
                'Created component from data: {0!r}.'.format(component_item)
            )

        session.commit()


class IntegratorPublishVersion(pyblish.api.ContextPlugin):
    '''Mark asset version as published.'''

    order = pyblish.api.IntegratorOrder + 0.2

    def process(self, context):
        '''Process *context*.'''
        asset_version = context.data['asset_version']
        session = asset_version.session

        asset_version['is_published'] = True
        session.commit()

        self.log.debug(
            'Set asset version {0!r} to published.'.format(asset_version)
        )


pyblish.api.register_plugin(IntegratorCreateAsset)
pyblish.api.register_plugin(IntegratorCreateComponents)
pyblish.api.register_plugin(IntegratorPublishVersion)
