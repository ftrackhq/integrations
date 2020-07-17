# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import ftrack_api

import nuke

from ftrack_connect_pipeline_nuke import plugin


class CollectNukeScenePlugin(plugin.PublisherCollectorNukePlugin):
    plugin_name = 'nukescene'

    def run(self, context=None, data=None, options=None):
        return [nuke.root().knob('name').value()]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CollectNukeScenePlugin(api_object)
    plugin.register()
