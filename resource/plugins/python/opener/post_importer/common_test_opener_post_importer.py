# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonDefaultOpenerPostImporterPlugin(plugin.OpenerPostImporterPlugin):
    '''Empty/passthrough opener post importer test/template plugin'''

    plugin_name = 'common_test_opener_post_importer'

    def run(self, context_data=None, data=None, options=None):
        return (
            {},
            {
                'message': 'No Data is imported this is for testing purposes',
                'data': ['abcde'],
            },
        )


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonDefaultOpenerPostImporterPlugin(api_object)
    plugin.register()
