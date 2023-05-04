# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonTestPublisherValidatorPlugin(plugin.PublisherValidatorPlugin):
    '''Publisher validator test/empty plugin'''

    plugin_name = 'common_test_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        return True


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonTestPublisherValidatorPlugin(api_object)
    plugin.register()
