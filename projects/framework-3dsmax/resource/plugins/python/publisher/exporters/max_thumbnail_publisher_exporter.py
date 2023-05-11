# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import uuid
import os

from pymxs import runtime as rt

from ftrack_connect_pipeline_3dsmax import plugin
import ftrack_api


class MaxThumbnailPublisherExporterPlugin(plugin.MaxPublisherExporterPlugin):
    plugin_name = 'max_thumbnail_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a Max thumbnail to a temp file for publish'''

        viewport_index = rt.viewport.activeViewport
        for collector in data:
            viewport_index = collector['result'][0]

        self.logger.debug(
            'Saving thumbnail of viewport {}...'.format(viewport_index)
        )
        bm = rt.viewport.getViewportDib(index=viewport_index)
        filename = '{0}.jpg'.format(uuid.uuid4().hex)
        path = os.path.join(rt.pathConfig.GetDir(rt.name("temp")), filename)
        bm.filename = path
        rt.save(bm)

        return [path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxThumbnailPublisherExporterPlugin(api_object)
    plugin.register()
