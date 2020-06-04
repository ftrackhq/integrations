# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os

from ftrack_connect_pipeline_nuke import plugin

class FileExistsValidatorPlugin(plugin.PublisherValidatorNukePlugin):
    plugin_name = 'file_exists'

    def run(self, context=None, data=None, options=None):
        scene_path = data[0]
        if os.path.exists(scene_path):
            return True
        else:
            self.logger.debug("Nuke Scene is not saved")
        return False


def register(api_object, **kw):
    plugin = FileExistsValidatorPlugin(api_object)
    plugin.register()
