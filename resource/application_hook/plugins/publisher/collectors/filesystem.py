# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin


class FilesystemCollectPlugin(plugin.CollectorPlugin):
    plugin_name = 'filesystem'

    def run(self, context=None, data=None, options=None):

        return [options['path']]


def register(api_object, **kw):
    plugin = FilesystemCollectPlugin(api_object)
    plugin.register()