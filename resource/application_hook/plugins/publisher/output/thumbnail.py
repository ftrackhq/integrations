# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import uuid

import MaxPlus

from ftrack_connect_pipeline_3dsmax import plugin


class ExtractThumbnailPlugin(plugin.ExtractorMaxPlugin):
    plugin_name = 'thumbnail'

    def run(self, context=None, data=None, options=None):
        component_name = options['component_name']
        view = MaxPlus.ViewportManager.GetActiveViewport()
        bm = MaxPlus.Factory.CreateBitmap()
        storage = MaxPlus.Factory.CreateStorage(7)
        info = storage.GetBitmapInfo()
        bm.SetStorage(storage)
        bm.DeleteStorage()
        res = view.GetDIB(info, bm)
        if not res:
            return

        filename = '{0}.jpg'.format(uuid.uuid4().hex)
        outpath = os.path.join(MaxPlus.PathManager.GetTempDir(), filename)
        info.SetName(outpath)
        bm.OpenOutput(info)
        bm.Write(info)
        bm.Close(info)
        return {component_name: outpath}


def register(api_object, **kw):
    plugin = ExtractThumbnailPlugin(api_object)
    plugin.register()
