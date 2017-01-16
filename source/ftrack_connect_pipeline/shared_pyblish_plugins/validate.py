# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import pyblish.api


class FtrackEnvironmentValidator(pyblish.api.Validator):

    label = "Ftrack environment"
    optional = False

    def process(self, context):
        self.log.debug('Validating ftrack environment')

        import os
        assert('FTRACK_SERVER' in os.environ)
        assert('FTRACK_SHOTID' in os.environ)
        assert('FTRACK_TASKID' in os.environ)


class FtrackLocationValidator(pyblish.api.Validator):

    label = "Valid Ftrack location"
    optional = False

    def process(self, context):
        self.log.debug('Validating ftrack location')

        import ftrack_api
        session = ftrack_api.Session()
        location = session.pick_location()
        self.log.debug('ftrack location = %s' % location['name'])
        assert(location['name'] != 'ftrack.unmanaged')

pyblish.api.register_plugin(FtrackEnvironmentValidator)
pyblish.api.register_plugin(FtrackLocationValidator)
