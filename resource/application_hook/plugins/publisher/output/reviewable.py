# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

import tempfile

import pymxs

from ftrack_connect_pipeline_3dsmax import plugin


class OutputReviewablePlugin(plugin.PublisherOutputMaxPlugin):
    plugin_name = 'reviewable'

    def run(self, context=None, data=None, options=None):
        pass


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = OutputReviewablePlugin(api_object)
    plugin.register()
