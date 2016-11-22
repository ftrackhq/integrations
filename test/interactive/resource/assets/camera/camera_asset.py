import ftrack_api

import ftrack_connect_pipeline.asset

IDENTIFIER = 'camera'


class PublishCamera(ftrack_connect_pipeline.asset.PyblishAsset):
    '''Handle publish of maya camera.'''

    def get_publish_items(self):
        '''Return list of items that can be published.'''
        options = []
        for instance in self.pyblish_context:
            if instance.data['family'] in ('camera', ):
                options.append({
                    'label': instance.name,
                    'name': instance.id,
                    'value': True
                })

        return options

    def get_item_options(self, name):
        '''Return options for publishable item with *name*.'''
        options = []
        for instance in self.pyblish_context:
            if instance.data['family'] in ('camera', ):
                options = [{
                    'type': 'boolean',
                    'label': 'Bake camera',
                    'name': 'bake_camera'
                }, {
                    'type': 'boolean',
                    'label': 'Lock camera',
                    'name': 'lock_camera'
                }]

        return options

    def get_options(self):
        '''Return global options for publishing.'''
        options = super(PublishCamera, self).get_options()
        options.append({
            'type': 'group',
            'name': 'camera_options',
            'label': 'Camera options',
            'options': [{
                'type': 'number',
                'label': 'Start frame',
                'name': 'start_frame_camera'
            }, {
                'type': 'number',
                'label': 'End frame',
                'name': 'end_frame_camera'
            }]
        })
        return options


def create_asset_publish():
    '''Return publish camera.'''
    return PublishCamera(
        description='publish maya cameras to ftrack.',
        asset_type_short='camera'
    )


def register(session):
    '''Subscribe to *session*.'''
    if not isinstance(session, ftrack_api.Session):
        return

    camera_asset = ftrack_connect_pipeline.asset.Asset(
        identifier=IDENTIFIER,
        label='Camera',
        icon='http://www.clipartbest.com/cliparts/9Tp/erx/9Tperxqrc.png',
        create_asset_publish=create_asset_publish
    )
    # Register camera asset on session. This makes sure that discover is called
    # for import and publish.
    camera_asset.register(session)
