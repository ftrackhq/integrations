# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import os

import pyblish.api

from ftrack_connect_pipeline import constant


class FtrackEnvironmentValidator(pyblish.api.Validator):

    label = "Validate Ftrack environment"
    optional = False

    def process(self, context):
        '''Validate basic ftrack environment variables.'''

        self.log.debug('Validating ftrack environment')

        assert('FTRACK_SERVER' in os.environ)
        assert('FTRACK_SHOTID' in os.environ)
        assert('FTRACK_TASKID' in os.environ)


class FtrackLocationValidator(pyblish.api.Validator):

    label = "Validate Ftrack location"
    optional = False

    def process(self, context):
        '''Run basic checks on the current location.'''

        self.log.debug('Validating ftrack location')

        import ftrack_api
        session = ftrack_api.Session()
        location = session.pick_location()
        assert(location['name'] != 'ftrack.unmanaged')


class AssetNameValidator(pyblish.api.Validator):

    label = "Validate Asset name"
    optional = False

    def process(self, context):
        '''Validate asset name.'''

        asset_options = context.data['options'][constant.ASSET_OPTION_NAME]
        asset_name = asset_options['asset_name']
        assert(asset_name != '')

pyblish.api.register_plugin(FtrackEnvironmentValidator)
pyblish.api.register_plugin(FtrackLocationValidator)
pyblish.api.register_plugin(AssetNameValidator)
