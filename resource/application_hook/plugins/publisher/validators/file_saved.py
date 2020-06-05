# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os

from ftrack_connect_pipeline_nuke import plugin

import nuke

class FileSavedValidatorPlugin(plugin.PublisherValidatorNukePlugin):
    plugin_name = 'file_saved'

    def run(self, context=None, data=None, options=None):
        if nuke.Root().name() != 'Root' and nuke.root().modified() != True:
            return True
        else:
            self.logger.debug("Nuke Scene is not saved")
        return False


def register(api_object, **kw):
    plugin = FileSavedValidatorPlugin(api_object)
    plugin.register()
