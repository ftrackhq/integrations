# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

import os
import uuid

import MaxPlus

from ftrack_connect_pipeline_3dsmax import plugin


class OutputThumbnailPlugin(plugin.PublisherOutputMaxPlugin):
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
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = OutputThumbnailPlugin(api_object)
    plugin.register()
