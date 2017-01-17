# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import os

import pyblish.api

from ftrack_connect_pipeline import constant


class FtrackEnvironmentValidator(pyblish.api.Validator):

    label = 'Validate Ftrack environment'
    optional = False

    def process(self, context):
        '''Validate basic ftrack environment variables.'''

        assert 'FTRACK_SERVER' in os.environ, 'FTRACK_SERVER environment variable not defined.'


class FtrackLocationValidator(pyblish.api.Validator):

    label = 'Validate Ftrack location'
    optional = False

    def process(self, context):
        '''Run basic checks on the current location.'''

        import ftrack_api
        session = ftrack_api.Session()
        location = session.pick_location()
        assert location['name'] != 'ftrack.unmanaged', 'Ftrack location is unmanaged.'


class AssetNameValidator(pyblish.api.Validator):

    label = 'Validate Asset name'
    optional = False

    def process(self, context):
        '''Validate asset name.'''

        try:
            asset_options = context.data['options'][constant.ASSET_OPTION_NAME]
            asset_name = asset_options['asset_name']
        except KeyError:
            asset_name = ''

        assert asset_name != '', 'Asset name is invalid.'


pyblish.api.register_plugin(FtrackEnvironmentValidator)
pyblish.api.register_plugin(FtrackLocationValidator)
pyblish.api.register_plugin(AssetNameValidator)
