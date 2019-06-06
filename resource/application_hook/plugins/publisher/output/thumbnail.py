# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import pymxs

from ftrack_connect_pipeline_3dsmax import plugin


class ExtractThumbnailPlugin(plugin.ExtractorMaxPlugin):
    plugin_name = 'thumbnail'

    def run(self, context=None, data=None, options=None):
        pass


def register(api_object, **kw):
    plugin = ExtractThumbnailPlugin(api_object)
    plugin.register()
