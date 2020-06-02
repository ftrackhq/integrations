# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline_nuke import plugin


class FtrackPublishNukePlugin(plugin.PublisherFinaliserNukePlugin):
    plugin_name = 'result.nuke'

    def run(self, context=None, data=None, options=None):
        return {}


def register(api_object, **kw):
    plugin = FtrackPublishNukePlugin(api_object)
    plugin.register()
