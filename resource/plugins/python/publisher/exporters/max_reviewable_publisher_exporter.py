# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os
import uuid

from pymxs import runtime as rt

from ftrack_connect_pipeline_3dsmax import plugin
import ftrack_api


class MaxReviewablePublisherExporterPlugin(plugin.MaxPublisherExporterPlugin):
    plugin_name = 'max_reviewable_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Export a Max reviewable to a temp file for publish'''
        viewport_index = rt.viewport.activeViewport
        for collector in data:
            viewport_index = collector['result'][0]

        self.logger.debug(
            'Saving AVI file of viewport {}...'.format(viewport_index)
        )

        filename = '{0}.avi'.format(uuid.uuid4().hex)
        path = os.path.join(rt.pathConfig.GetDir(rt.name("temp")), filename)
        view_size = rt.getViewSize()
        anim_bmp = rt.bitmap(view_size.x, view_size.y, filename=path)
        for t in range(int(rt.animationRange.start), int(rt.animationRange.end)):
            rt.sliderTime = t
            dib = rt.viewport.getViewportDib(index=viewport_index)
            rt.copy(dib, anim_bmp)
            rt.save(anim_bmp)
        rt.close(anim_bmp)
        rt.gc()
        return [path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxReviewablePublisherExporterPlugin(api_object)
    plugin.register()
