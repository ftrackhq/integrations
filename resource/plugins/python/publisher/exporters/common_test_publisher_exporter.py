# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import shutil
import tempfile
from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonTestPublisherExporterPlugin(plugin.PublisherExporterPlugin):
    '''Publisher test/template exporter plugin'''

    plugin_name = 'common_test_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        return []


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonTestPublisherExporterPlugin(api_object)
    plugin.register()
