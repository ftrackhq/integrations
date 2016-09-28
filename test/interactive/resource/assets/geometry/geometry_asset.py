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

    def prepare_publish(self):
        '''Prepare publish and populate with items.'''
        publish_data = super(PublishGeometry, self).prepare_publish()
        # Loop over maya scene and scan for maya models to publish.
        publish_data['items'] = ['maya_model_xyz']
        return publish_data

    def get_publish_items(self, publish_data):
        '''Return list of items that can be published.'''
        # Loop items and create a list of what can be published.
        options = []
        for item in publish_data['items']:
            options.append({
                'label': item,
                'name': item,
                'value': True
            })

        return options

    def get_item_options(self, publish_data, name):
        '''Return options for publishable item with *name*.'''
        # Return options, if any, for a geometry with the given name name.
        options = [{
            'type': 'boolean',
            'label': 'Do stuff with geometry',
            'name': 'do_stuff_geometry'
        }]

        return options

    def publish(self, publish_data):
        '''Publish or raise exception if not valid.'''
        # Publish asset based on options in publish_data.
        print 'Publish using', publish_data


def register(session):
    '''Subscribe to *session*.'''
    if not isinstance(session, ftrack_api.Session):
        return

    geometry_asset = ftrack_connect_pipeline.asset.Asset(
        identifier=IDENTIFIER,
        import_asset=ImportGeometry(),
        publish_asset=PublishGeometry(
            label='Geometry',
            description='Publish maya geometry to ftrack.',
            icon='http://www.clipartbest.com/cliparts/9Tp/erx/9Tperxqrc.png'
        )
    )
    # Register geometry asset on session. This makes sure that discover is
    # called for import and publish.
    geometry_asset.register(session)
