# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import nuke

from ftrack_connect_pipeline_nuke import plugin


class CollectNukeScenePlugin(plugin.CollectorNukePlugin):
    plugin_name = 'nukescene'

    def run(self, context=None, data=None, options=None):
        return [nuke.root().knob('name').value()]


def register(api_object, **kw):
    plugin = CollectNukeScenePlugin(api_object)
    plugin.register()

