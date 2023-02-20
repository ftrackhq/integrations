# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
import ftrack_api


class CommonPassthroughPublisherExporterPlugin(plugin.PublisherExporterPlugin):
    '''Passthrough publisher exporter plugin'''

    plugin_name = 'common_passthrough_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Pass through the collected result supplied with *data*'''
        output = self.output
        for collector in data:
            output.append(collector['result'][0])

        return output


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonPassthroughPublisherExporterPlugin(api_object)
    plugin.register()
