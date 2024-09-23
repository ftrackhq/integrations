# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import (
    PluginUIHookExecutionError,
    PluginExecutionError,
)


class BatchCollectorPlugin(BasePlugin):
    name = 'batch_collector'

    def ui_hook(self, payload):
        '''
        Collect all objects from the given source folder and return them
        '''
        # Collect objects and necessary data for the UI in here
        source_folder = payload['source_folder']
        collected_objects = []
        # Pick all files from the folder and return name and path
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                print(os.path.join(root, file))
                collected_objects.append(
                    {'obj_name': file, 'obj_path': os.path.join(root, file)}
                )

        return collected_objects

    def run(self, store):
        '''
        Collect objects path and store them in the given store
        '''
        collected_objects = self.options.get('collected_objects')
        if not collected_objects:
            raise PluginExecutionError('Please collect objects first')
        store['collected_objects'] = collected_objects
