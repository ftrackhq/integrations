# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os

import pyblish.api

from ftrack_connect_pipeline import constant


class IntegratorCreateAsset(pyblish.api.ContextPlugin):
    '''Create asset and prepare publish.'''

    order = pyblish.api.IntegratorOrder

    def process(self, context):
        '''Process *context* create asset.'''
        ftrack_entity = context.data['ftrack_entity']
        session = ftrack_entity.session

        asset_options = context.data['options'][constant.ASSET_OPTION_NAME]
        asset_type_id = asset_options['asset_type']
        asset_name = asset_options['asset_name']
        comment = context.data['options'].get(
            constant.ASSET_VERSION_COMMENT_OPTION_NAME,
            ''
        )

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

        thumbnail_path = context.data['options'].get('thumbnail')

        if thumbnail_path and os.path.isfile(thumbnail_path):
            self.log.debug(
                'Got thumbnail from options: {0!r}.'.format(
                    thumbnail_path
                )
            )
            asset_version.create_thumbnail(thumbnail_path)
            session.commit()
        else:
            self.log.debug(
                'Thumbnail file did not exist: {0!r}.'.format(
                    thumbnail_path
                )
            )

        context.data['asset_version'] = asset_version

        self.log.debug('Created asset version {0!r}.'.format(asset_version))


class IntegratorCreateComponents(pyblish.api.InstancePlugin):
    '''Extract nuke cameras from scene.'''

    order = pyblish.api.IntegratorOrder + 0.1

    families = ['ftrack']
    match = pyblish.api.Subset

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
            new_component = session.create_component(
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

            # Save authoring software information (name, version, ...)
            # into the component metadata, if available.
            if 'software' in context.data:
                self.log.debug('Found software metadata.')
                self.log.debug('Software = {0}'.format(context.data['software']))
                new_component['metadata']['software'] = context.data['software']['name']
                new_component['metadata']['software_version'] = context.data['software']['version']
            else:
                self.log.debug('No software metadata found.')

        session.commit()


class IntegratorCreateReviewableComponents(pyblish.api.InstancePlugin):
    '''Extract and publish available reviewable component.'''

    order = pyblish.api.IntegratorOrder + 0.2

    families = constant.REVIEW_FAMILY_PYBLISH
    match = pyblish.api.Subset

    def process(self, instance):
        '''Process *context* and create reviwable components.'''
        for component_item in instance.data.get(
            'ftrack_web_reviewable_components', []
        ):
            asset_version = instance.context.data['asset_version']
            session = asset_version.session

            asset_version.encode_media(component_item['path'])
            session.commit()
            self.log.debug(
                'Reviewable component {0!r} published.'.format(
                    component_item
                )
            )

            # Only one is allowed.
            break
        else:
            self.log.debug(
                'No reviewable component found to publish.'
            )


class IntegratorPublishVersion(pyblish.api.ContextPlugin):
    '''Mark asset version as published.'''

    order = pyblish.api.IntegratorOrder + 0.3

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
pyblish.api.register_plugin(IntegratorCreateReviewableComponents)
pyblish.api.register_plugin(IntegratorPublishVersion)
