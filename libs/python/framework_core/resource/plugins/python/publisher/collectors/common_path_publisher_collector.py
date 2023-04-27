# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonPathPublisherCollectorPlugin(plugin.PublisherCollectorPlugin):
    '''Standalone publisher path collector plugin'''

    plugin_name = 'common_path_publisher_collector'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch the test path'''
        return "example/path/to/your/file.txt"

    def run(self, context_data=None, data=None, options=None):
        '''Supply the path given in *options* to standalone'''
        output = self.output
        output.append(options['path'])
        return output


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonPathPublisherCollectorPlugin(api_object)
    plugin.register()
