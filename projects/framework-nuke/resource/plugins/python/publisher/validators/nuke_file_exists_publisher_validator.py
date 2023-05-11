# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api
import os

from ftrack_connect_pipeline_nuke import plugin


class NukeFileExistsPublisherValidatorPlugin(
    plugin.NukePublisherValidatorPlugin
):
    '''Nuke file exists publisher validator plugin'''

    plugin_name = 'nuke_file_exists_publisher_validator'

    def run(self, context_data=None, data=None, options=None):
        '''Return true if the file path pointed out by collected object in *data* exist'''
        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        if len(collected_objects) == 0:
            msg = 'No nodes selected!'
            self.logger.error(msg)
            return (False, {'message': msg})

        scene_path = collected_objects[0]
        if os.path.exists(scene_path):
            return True
        else:
            self.logger.debug("Nuke Scene file does not exists")
        return False


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeFileExistsPublisherValidatorPlugin(api_object)
    plugin.register()
