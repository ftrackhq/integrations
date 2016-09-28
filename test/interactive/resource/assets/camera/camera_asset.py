import ftrack_api

import ftrack_connect_pipeline.asset

IDENTIFIER = 'camera'


class ImportCamera(ftrack_connect_pipeline.asset.ImportAsset):
    '''Handle import of maya camera.'''

    def discover(self, event):
        '''Discover import camera.'''
        asset_type_short = (
            event['component']['version']['asset']['asset_type']['short']
        )
        if asset_type_short == 'camera':
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


class PublishCamera(ftrack_connect_pipeline.asset.PyblishAsset):
    '''Handle publish of maya camera.'''

    def get_publish_items(self, publish_data):
        '''Return list of items that can be published.'''
        options = []
        for instance in publish_data:
            if instance.data['family'] in ('camera', ):
                options.append({
                    'label': instance.name,
                    'name': instance.id,
                    'value': True
                })

        return options

    def get_item_options(self, publish_data, name):
        '''Return options for publishable item with *name*.'''
        options = []
        for instance in publish_data:
            if instance.data['family'] in ('camera', ):
                options = [{
                    'type': 'boolean',
                    'label': 'Bake camera',
                    'name': 'bake_camera'
                }, {
                    'type': 'boolean',
                    'label': 'Lock camera',
                    'name': 'lock_camera'
                }, {
                    'type': 'number',
                    'label': 'Start frame',
                    'name': 'start_frame_camera'
                }, {
                    'type': 'number',
                    'label': 'End frame',
                    'name': 'end_frame_camera'
                }]

        return options


def register(session):
    '''Subscribe to *session*.'''
    if not isinstance(session, ftrack_api.Session):
        return

    camera_asset = ftrack_connect_pipeline.asset.Asset(
        identifier=IDENTIFIER,
        import_asset=ImportCamera(),
        publish_asset=PublishCamera(
            label='Camera',
            description='publish maya cameras to ftrack.',
            icon='http://www.clipartbest.com/cliparts/9Tp/erx/9Tperxqrc.png'
        )
    )
    # Register camera asset on session. This makes sure that discover is called
    # for import and publish.
    camera_asset.register(session)
