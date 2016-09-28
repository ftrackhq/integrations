import os
import logging

import pyblish
import pyblish.plugin
import pyblish.api
import pyblish.util
import ftrack_api

import ftrack_connect_pipeline.asset

IDENTIFIER = 'camera'

logging.basicConfig(level=logging.INFO)


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


class PublishCamera(ftrack_connect_pipeline.asset.PublishAsset):
    '''Handle publish of maya camera.'''

    icon_url = 'http://www.clipartbest.com/cliparts/9Tp/erx/9Tperxqrc.png'

    label = 'Camera'

    description = 'publish maya cameras to ftrack.'

    def __init__(self):
        '''Instantiate and let pyblish know about the plugins.'''
        pyblish.plugin.register_plugin_path(
            os.path.normpath(
                os.path.join(
                    os.path.abspath(
                        os.path.dirname(__file__)
                    ),
                    '..',
                    'pyblish_plugin'
                )
            )
        )

    def prepare_publish(self):
        '''Return context for publishing.'''
        context = pyblish.api.Context()
        context = pyblish.util.collect(context=context)
        return context

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

        logging.info('Building interface from {0}'.format(options))

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

    def get_options(self, publish_data):
        '''Return general options for.'''
        # Get options like asset type etc. from super class.
        options = super(PublishCamera, self).get_options(publish_data)
        
        from ftrack_connect_pipeline.ui.widget import asset_selector
        asset_selector = asset_selector.AssetSelector(
            publish_data.data['ftrack_entity']
        )

        def handle_change(value):
            publish_data.data['options'] = {}
            publish_data.data['options']['asset_name'] = value['asset_name']
            publish_data.data['options']['asset_type'] = value['asset_type']

        asset_selector.asset_changed.connect(handle_change)

        return asset_selector

    def publish(self, publish_data, options):
        '''Publish or raise exception if not valid.'''
        publish_data['options'] = options
        pyblish.util.validate(publish_data)
        pyblish.util.integrate(publish_data)
        pyblish.util.extract(publish_data)


def register(session):
    '''Subscribe to *session*.'''
    if not isinstance(session, ftrack_api.Session):
        return

    camera_asset = ftrack_connect_pipeline.asset.Asset(
        identifier=IDENTIFIER,
        import_asset=ImportCamera(),
        publish_asset=PublishCamera()
    )
    # Register camera asset on session. This makes sure that discover is called
    # for import and publish.
    camera_asset.register(session)
