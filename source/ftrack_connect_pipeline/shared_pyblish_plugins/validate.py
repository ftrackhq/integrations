# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import os

import pyblish.api

from ftrack_connect_pipeline import constant


class FtrackEnvironmentValidator(pyblish.api.Validator):
    '''Validate ftrack environment variables.'''

    label = 'Validate ftrack environment'
    optional = False

    def process(self, context):
        '''Check that some basic ftrack environment variables are defined.'''

        assert 'FTRACK_SERVER' in os.environ, (
               'FTRACK_SERVER environment variable not defined.'
        )


class FtrackLocationValidator(pyblish.api.Validator):
    '''Validate Ftrack location.'''

    label = 'Validate ftrack location'
    optional = False

    def process(self, context):
        '''Check that the Ftrack location is not unmanaged.'''

        import ftrack_api
        session = ftrack_api.Session()
        location = session.pick_location()
        assert location['name'] != 'ftrack.unmanaged', (
               'Ftrack location is unmanaged.'
        )


class AssetNameValidator(pyblish.api.Validator):
    '''Validate asset names.'''

    label = 'Validate asset name'
    optional = False

    def process(self, context):
        '''Check that the asset name is not empty.'''

        try:
            asset_options = context.data['options'][constant.ASSET_OPTION_NAME]
            asset_name = asset_options['asset_name']
        except KeyError:
            asset_name = ''

        assert asset_name != '', (
               'Asset name is empty.'
        )


pyblish.api.register_plugin(FtrackEnvironmentValidator)
pyblish.api.register_plugin(FtrackLocationValidator)
pyblish.api.register_plugin(AssetNameValidator)
