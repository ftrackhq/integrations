# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import uuid
import MaxPlus

from ftrack_connect_pipeline_3dsmax import plugin


class ExtractThumbnailPlugin(plugin.ExtractorMaxPlugin):
    plugin_name = 'thumbnail'

    def run(self, context=None, data=None, options=None):
        viewport_index = data[0]
        MaxPlus.ViewportManager.SetActiveViewport(viewport_index)
        MaxPlus.ViewportManager.SetViewportMax(True)

        filename = '{0}.jpg'.format(uuid.uuid4().hex)
        outpath = os.path.join(MaxPlus.PathManager.GetTempDir(), filename)
        render = MaxPlus.RenderSettings
        render.SetOutputFile(outpath)
        render.SetSaveFile(True)

        MaxPlus.RenderExecute.QuickRender()

        return outpath


def register(api_object, **kw):
    plugin = ExtractThumbnailPlugin(api_object)
    plugin.register()
