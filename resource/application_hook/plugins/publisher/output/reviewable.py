# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import tempfile

import pymxs

from ftrack_connect_pipeline_3dsmax import plugin


class OutputReviewablePlugin(plugin.PublisherOutputMaxPlugin):
    plugin_name = 'reviewable'

    def run(self, context=None, data=None, options=None):
        pass


def register(api_object, **kw):
    plugin = OutputReviewablePlugin(api_object)
    plugin.register()
