# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import ftrack_connect_pipeline
from ftrack_connect_pipeline.ui.widget.field import asset_selector
from ftrack_connect_pipeline import constant


import logging


class Asset(object):
    '''Manage assets.'''

    def __init__(
        self, identifier, icon, label, create_asset_publish=None,
        create_asset_import=None
    ):
        '''Instantiate with manager for publish and import.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.logger.debug(
            'Registering new asset: {0!r}.'.format(identifier)
        )
        self.icon = icon
        self.label = label

        self.create_asset_publish = create_asset_publish
        self.create_asset_import = create_asset_import
        self.identifier = identifier

    def discover_publish(self, event):
        '''Discover publish camera.'''
        item = {
            'items': [{
                'label': self.label,
                'icon': self.icon,
                'actionIdentifier': self.identifier
            }]
        }
        return item

    def launch_publish(self, event):
        '''Callback method for publish action.'''
        publish_asset = self.create_asset_publish()
        return {
            'success': True,
            'message': '',
            'publish_asset': publish_asset
        }

    def register(self, session):
        '''Register listeners on *session*.'''
        self._session = session

        self._session.event_hub.subscribe(
            'topic=ftrack.action.discover',
            self.discover_publish
        )

        self._session.event_hub.subscribe(
            'topic=ftrack.action.launch and data.actionIdentifier={0}'.format(
                self.identifier
            ),
            self.launch_publish
        )


class ImportAsset(object):
    '''Manage import of an asset.'''

    def discover(self, event):
        '''Discover import camera.'''
        raise NotImplementedError()

    def get_options(self, component):
        '''Return import options from *component*.'''
        return []

    def import_asset(self, component, options):
        '''Import *component* based on *options*.'''
        raise NotImplementedError()


class PublishAsset(object):
    '''Manage publish of an asset.'''

    def __init__(
        self, description, asset_type_short=None,
        enable_scene_as_reference=True,
        enable_reviewable_component=True
    ):
        '''Instantiate publish asset with *label* and *description*.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.description = description
        self.asset_type_short = asset_type_short
        self.enable_scene_as_reference = enable_scene_as_reference
        self.enable_reviewable_component = enable_reviewable_component

    def discover(self, event):
        '''Discover import camera.'''
        raise NotImplementedError()

    def prepare_publish(self):
        '''Return context for publishing.'''
        plugin = ftrack_connect_pipeline.get_plugin()
        self.ftrack_entity = plugin.get_context()
        self.publish_data = dict()

    def get_publish_items(self):
        '''Return list of items that can be published.'''
        return []

    def get_reviewable_items(self):
        '''Return a list of reviewable items.'''
        return []

    def get_item_options(self, key):
        '''Return options for publishable item with *key*.'''
        return []

    def get_options(self):
        '''Return general options for.'''

        plugin = ftrack_connect_pipeline.get_plugin()
        context = plugin.get_context()
        if isinstance(context, context.session.types['Task']):
            # Publish to task parent.
            context = context['parent']

        asset_selector_widget = asset_selector.AssetSelector(
            context, hint=self.asset_type_short
        )

        from ftrack_connect_pipeline.ui.widget.field import thumbnail

        thumbnail = thumbnail.ThumbnailField()

        options = [
            {
                'widget': asset_selector_widget,
                'name': constant.ASSET_OPTION_NAME,
                'type': 'qt_widget'
            },
            {
                'widget': thumbnail,
                'name': 'thumbnail',
                'type': 'qt_widget'
            },
            {
                'label': '',
                'name': constant.ASSET_VERSION_COMMENT_OPTION_NAME,
                'type': 'textarea',
                'empty_text': 'Please add a description...'
            }
        ]

        if self.enable_scene_as_reference:
            options.append({
                'label': 'Attach scene as reference',
                'name': constant.SCENE_AS_REFERENCE_OPTION_NAME,
                'type': 'boolean'
            })

        if self.enable_reviewable_component:
            reviewable_items = self.get_reviewable_items()
            if reviewable_items:
                reviewable_items.insert(
                    0,
                    {
                        'label': '-- No reviewable --',
                        'value': None
                    }
                )
                options.append({
                    'type': 'group',
                    'label': 'Web reviewable',
                    'name': constant.REVIEWABLE_OPTION_NAME,
                    'options': [{
                        'type': 'enumerator',
                        'name': constant.REVIEWABLE_COMPONENT_OPTION_NAME,
                        'label': 'Generate from',
                        'data': reviewable_items
                    }]
                })

        self.logger.debug('Context option: {0!r}.'.format(options))
        return options

    def publish(self, item_options, general_options, selected_items):
        '''Publish or raise exception if not valid.'''
        raise NotImplementedError()

    def get_scene_selection(self):
        '''Return a list of names for scene selection.'''
        raise NotImplementedError()

    def get_entity(self):
        '''Return the current context entity.'''
        return self.ftrack_entity

    def switch_entity(self, entity):
        '''Change current context of **publish_data* to the given *entity*.'''
        self.ftrack_entity = entity
