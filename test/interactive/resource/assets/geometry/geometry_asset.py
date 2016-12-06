import ftrack_api

import ftrack_connect_pipeline.asset

IDENTIFIER = 'geometry'


class ImportGeometry(ftrack_connect_pipeline.asset.ImportAsset):
    '''Handle import of maya geometry.'''

    def discover(self, event):
        '''Discover import geometry.'''
        asset_type_short = (
            event['component']['version']['asset']['asset_type']['short']
        )
        if asset_type_short == 'geometry':
            return {
                'label': 'Import as reference',
                'identifier': IDENTIFIER
            }

    def get_options(self, component):
        '''Return import options from *component*.'''
        return []

    def import_asset(self, component, options):
        '''Import *component* based on *options*.'''
        pass


class PublishGeometry(ftrack_connect_pipeline.asset.PublishAsset):
    '''Handle publish of maya geometry.'''

    def prepare_publish(self, ftrack_entity):
        '''Prepare publish and populate with items.'''
        super(PublishGeometry, self).prepare_publish(ftrack_entity)
        # Loop over maya scene and scan for maya models to publish.
        self.publish_items = ['maya_model_xyz', 'some_other_model', 'foo']

    def get_publish_items(self):
        '''Return list of items that can be published.'''
        # Loop items and create a list of what can be published.
        options = []
        for item in self.publish_items:
            options.append({
                'label': item,
                'name': item,
                'value': True
            })

        return options

    def get_item_options(self, name):
        '''Return options for publishable item with *name*.'''
        # Return options, if any, for a geometry with the given name name.
        options = [{
            'type': 'boolean',
            'label': 'Do stuff with geometry',
            'name': 'do_stuff_geometry'
        }]

        return options

    def publish(self, item_options, general_options, selected_items):
        '''Publish or raise exception if not valid.'''
        # Publish asset based using options.
        print 'Publish using', item_options, general_options, selected_items
        return {
            'success': True,
            'asset_version': None
        }

    def get_scene_selection(self):
        '''Return a list of names for scene selection.'''
        return ['foo', 'some_other_model']


def create_asset_publish():
    '''Return new asset publisher.'''
    return PublishGeometry(
        description='Publish maya geometry to ftrack.',
        asset_type_short='geo'
    )


def create_asset_import():
    '''Return new asset import.'''
    return ImportGeometry()


def register(session):
    '''Subscribe to *session*.'''
    if not isinstance(session, ftrack_api.Session):
        return

    geometry_asset = ftrack_connect_pipeline.asset.Asset(
        identifier=IDENTIFIER,
        label='Geometry',
        icon='http://www.clipartbest.com/cliparts/9Tp/erx/9Tperxqrc.png',
        create_asset_import=create_asset_import,
        create_asset_publish=create_asset_publish
    )
    # Register geometry asset on session. This makes sure that discover is
    # called for import and publish.
    geometry_asset.register(session)
